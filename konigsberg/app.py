import flask

import flowers

app = flask.Flask(__name__)

florist = flowers.Florist('bingraph')


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
    conference_series_ids = _get_ids_from_request('conference-series-ids')
    paper_ids = _get_ids_from_request('paper-ids')

    self_citations = _get_bool_from_request('self-citations')
    exclude_coauthors = _get_bool_from_request('exclude-coauthors')

    pub_years = _get_range_from_request('pub-years')
    cit_years = _get_range_from_request('cit-years')

    max_results = _get_int_from_request('max-results')

    flower = florist.get_flower(
        author_ids=author_ids, affiliation_ids=affiliation_ids,
        field_of_study_ids=field_of_study_ids, journal_ids=journal_ids,
        conference_series_ids=conference_series_ids, paper_ids=paper_ids,
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
    conference_series_ids = _get_ids_from_request('conference-series-ids')
    paper_ids = _get_ids_from_request('paper-ids')

    stats = florist.get_stats(
        author_ids=author_ids, affiliation_ids=affiliation_ids,
        field_of_study_ids=field_of_study_ids, journal_ids=journal_ids,
        conference_series_ids=conference_series_ids, paper_ids=paper_ids,
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
    conference_series_ids = _get_ids_from_request('conference-series-ids')
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
        conference_series_ids=conference_series_ids, paper_ids=paper_ids,
        self_citations=self_citations, coauthors=not exclude_coauthors,
        pub_years=pub_years, cit_years=cit_years,
        allow_not_found=True, max_results=max_results)

    return flask.jsonify(node_info)


if __name__ == '__main__':
    app.run('127.0.0.1', port=8081, debug=True)
