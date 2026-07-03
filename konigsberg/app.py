import logging
import os
import threading
import time

import flask

from . import flowers

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
if not log.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        '[%(asctime)s] [warmup] %(message)s'))
    log.addHandler(_h)

app = flask.Flask(__name__)

log.info('instantiating Florist...')
_t0 = time.monotonic()
florist = flowers.Florist('bingraph-openalex')
log.info('Florist ready in %.1fs', time.monotonic() - _t0)


def _jit_warmup():
    """Trigger Numba JIT compilation on module import.

    Uses author at index 0 (least prolific) so the compile step is fast
    and touches every code path but only a tiny working set. Numba
    cache=True means this is a load-from-disk on subsequent restarts.
    """
    if florist.author_range == 0:
        log.warning('empty author range; skipping warmup')
        return
    first_entity_id = int(florist.entity_ind2id_map.arrs[0])
    steps = [
        ('get_names', lambda: florist.get_names(
            'authors', [first_entity_id])),
        ('get_stats', lambda: florist.get_stats(
            author_ids=[first_entity_id], allow_not_found=True)),
        ('get_flower', lambda: florist.get_flower(
            author_ids=[first_entity_id],
            allow_not_found=True, max_results=1)),
    ]
    if len(florist.paper_ind2id_map.arrs) > 0:
        first_paper_id = int(florist.paper_ind2id_map.arrs[0])
        steps.append(('get_paper_info', lambda: florist.get_paper_info(
            [first_paper_id])))
        steps.append(('get_paper_citations',
                      lambda: florist.get_paper_citations([first_paper_id])))
    for name, fn in steps:
        t = time.monotonic()
        try:
            fn()
            log.info('JIT %s ok (%.1fs)', name, time.monotonic() - t)
        except Exception as e:  # noqa: BLE001
            log.warning('JIT %s failed after %.1fs: %s',
                        name, time.monotonic() - t, e)


def _page_cache_warmup():
    """Prefault paper2entity + paper2citor-citee pages for popular authors.

    Runs in a background thread when KONIGSBERG_WARMUP_COUNT > 0.
    Sleeps KONIGSBERG_WARMUP_DELAY_SECS between authors so live user
    requests get their fair share of disk I/O. Disabled by default
    because on cold cache each warmup step reads ~500 MB of random
    pages, and running them back-to-back starves real requests enough
    to trip webapp's 300 s timeout.
    """
    n = int(os.getenv('KONIGSBERG_WARMUP_COUNT', '0'))
    if n <= 0 or florist.author_range == 0:
        return
    delay = int(os.getenv('KONIGSBERG_WARMUP_DELAY_SECS', '30'))
    ind2id = florist.entity_ind2id_map.arrs
    # Authors are at indices [0, author_range); rank ascending means the
    # last N are the most productive.
    top_indices = list(range(
        max(0, int(florist.author_range) - n),
        int(florist.author_range)))
    log.info('page-cache warmup: %d authors, %ds between',
             len(top_indices), delay)
    for i, ind in enumerate(reversed(top_indices)):
        try:
            author_id = int(ind2id[ind])
        except Exception:
            continue
        t = time.monotonic()
        try:
            florist.get_flower(
                author_ids=[author_id], allow_not_found=True, max_results=50)
            florist.get_stats(
                author_ids=[author_id], allow_not_found=True)
            log.info(
                'page-cache %d/%d: author %d warmed in %.1fs',
                i + 1, n, author_id, time.monotonic() - t)
        except Exception as e:  # noqa: BLE001
            log.warning('page-cache warmup for %d failed: %s',
                        author_id, e)
        if delay > 0 and i + 1 < len(top_indices):
            time.sleep(delay)


if os.getenv('KONIGSBERG_SKIP_WARMUP') == '1':
    log.info('KONIGSBERG_SKIP_WARMUP=1 set; skipping warmup')
else:
    _jit_warmup()
    # Kick off page-cache warmup in background so container starts
    # serving right away. Log progress.
    threading.Thread(target=_page_cache_warmup, daemon=True,
                     name='page-cache-warmup').start()


def _get_ids_from_request(argname):
    ids_str = flask.request.args.get(argname, '')
    try:
        return list(map(int, filter(None, ids_str.split(','))))
    except ValueError:
        flask.abort(400)


def _get_id_from_request(argname):
    try:
        return int(flask.request.args.get(argname, ''))
    except ValueError:
        flask.abort(400)


def _get_bool_from_request(argname):
    return bool(flask.request.args.get(argname, ''))


def _get_range_from_request(argname):
    range_str = flask.request.args.get(argname, '')
    if not range_str:
        return None
    try:
        start_year, end_year = range_str.split(',')
        start_year = int(start_year)
        end_year = int(end_year)
    except ValueError:
        flask.abort(400)
    return start_year, end_year


def _get_int_from_request(argname):
    int_str = flask.request.args.get(argname, '')
    if not int_str:
        return None
    try:
        return int(int_str)
    except ValueError:
        flask.abort(400)


def result_arrays_as_dict(result_arrays):
    ids = tuple(map(int, result_arrays.ids))
    citor_scores = tuple(map(float, result_arrays.citor_scores))
    citee_scores = tuple(map(float, result_arrays.citee_scores))
    coauthors = tuple(map(bool, result_arrays.coauthors))
    kinds = tuple(map(int, result_arrays.kinds))
    total = int(result_arrays.total)
    return dict(ids=ids, citor_scores=citor_scores, citee_scores=citee_scores,
                coauthors=coauthors, kinds=kinds, total=total)


def stringify_keys(d):
    # Convert keys from integers to strings so JSON can encode them.
    return dict(zip(map(str, d.keys()), d.values()))


def pub_year_counts_as_json_dict(pub_year_counts):
    return stringify_keys(pub_year_counts)


def cit_year_counts_as_json_dict(cit_year_counts):
    return dict(zip(map(str, cit_year_counts.keys()),
                    map(stringify_keys, cit_year_counts.values())))


def flower_as_dict(flower):
    return dict(
        author=result_arrays_as_dict(flower.author),
        affiliation=result_arrays_as_dict(flower.affiliation),
        field_of_study=result_arrays_as_dict(flower.field_of_study),
        venue=result_arrays_as_dict(flower.venue))


def stats_as_dict(stats):
    return dict(
        pub_year_counts=pub_year_counts_as_json_dict(stats.pub_year_counts),
        cit_year_counts=cit_year_counts_as_json_dict(stats.cit_year_counts),
        pub_count=stats.pub_count,
        cit_count=stats.cit_count,
        ref_count=stats.ref_count)


@app.route('/get-flower')
def get_flower():
    author_ids = _get_ids_from_request('author-ids')
    affiliation_ids = _get_ids_from_request('affiliation-ids')
    field_of_study_ids = _get_ids_from_request('field-of-study-ids')
    journal_ids = _get_ids_from_request('journal-ids')
    paper_ids = _get_ids_from_request('paper-ids')

    self_citations = _get_bool_from_request('self-citations')
    exclude_coauthors = _get_bool_from_request('exclude-coauthors')

    pub_years = _get_range_from_request('pub-years')
    cit_years = _get_range_from_request('cit-years')

    max_results = _get_int_from_request('max-results')

    flower = florist.get_flower(
        author_ids=author_ids, affiliation_ids=affiliation_ids,
        field_of_study_ids=field_of_study_ids, journal_ids=journal_ids,
        paper_ids=paper_ids,
        self_citations=self_citations, coauthors=not exclude_coauthors,
        pub_years=pub_years, cit_years=cit_years,
        allow_not_found=True, max_results=max_results)

    return flask.jsonify(flower_as_dict(flower))


@app.route('/get-stats')
def get_stats():
    author_ids = _get_ids_from_request('author-ids')
    affiliation_ids = _get_ids_from_request('affiliation-ids')
    field_of_study_ids = _get_ids_from_request('field-of-study-ids')
    journal_ids = _get_ids_from_request('journal-ids')
    paper_ids = _get_ids_from_request('paper-ids')

    stats = florist.get_stats(
        author_ids=author_ids, affiliation_ids=affiliation_ids,
        field_of_study_ids=field_of_study_ids, journal_ids=journal_ids,
        paper_ids=paper_ids,
        allow_not_found=True)

    return flask.jsonify(stats_as_dict(stats))


@app.route('/get-node-info')
def get_node_info():
    node_id = _get_id_from_request('node-id')
    node_type = _get_int_from_request('node-type')

    author_ids = _get_ids_from_request('author-ids')
    affiliation_ids = _get_ids_from_request('affiliation-ids')
    field_of_study_ids = _get_ids_from_request('field-of-study-ids')
    journal_ids = _get_ids_from_request('journal-ids')
    paper_ids = _get_ids_from_request('paper-ids')

    self_citations = _get_bool_from_request('self-citations')
    exclude_coauthors = _get_bool_from_request('exclude-coauthors')

    pub_years = _get_range_from_request('pub-years')
    cit_years = _get_range_from_request('cit-years')

    max_results = _get_int_from_request('max-results')

    node_info = florist.get_node_info(
        node_id=node_id, node_type=node_type,
        author_ids=author_ids, affiliation_ids=affiliation_ids,
        field_of_study_ids=field_of_study_ids, journal_ids=journal_ids,
        paper_ids=paper_ids,
        self_citations=self_citations, coauthors=not exclude_coauthors,
        pub_years=pub_years, cit_years=cit_years,
        allow_not_found=True, max_results=max_results)

    return flask.jsonify(node_info)


@app.route('/get-names')
def get_names():
    entity_type = flask.request.args.get('type', '')
    ids = _get_ids_from_request('ids')
    try:
        result = florist.get_names(entity_type, ids)
    except ValueError:
        flask.abort(400)
    return flask.jsonify(stringify_keys(result))


@app.route('/get-paper-info')
def get_paper_info():
    ids = _get_ids_from_request('ids')
    result = florist.get_paper_info(ids)
    return flask.jsonify(stringify_keys(result))


@app.route('/get-paper-citations')
def get_paper_citations():
    ids = _get_ids_from_request('ids')
    result = florist.get_paper_citations(ids)
    return flask.jsonify(stringify_keys(result))


if __name__ == '__main__':
    app.run('127.0.0.1', port=8081, debug=True)
