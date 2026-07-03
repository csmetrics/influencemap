import hashlib
import logging
import os
import pathlib
import pickle
import sys
import time

import requests


# --- Response cache --------------------------------------------------------
#
# /get-flower and /get-stats are expensive on cold page cache (60-120s for
# a productive author). Cache the parsed JSON per parameter-set so the
# only requests that hit konigsberg are truly new. Complements the
# outer HTML cache in webapp/views.py — this layer helps when the URL
# changes filters (year range, coauthor toggle) but the underlying
# konigsberg call is the same.

_KB_CACHE_DIR = pathlib.Path(
    os.getenv('KB_CACHE_DIR', '/influencemap/logs/kb_cache'))
_KB_CACHE_TTL_SECS = int(os.getenv('KB_CACHE_TTL_SECS', str(7 * 24 * 3600)))
try:
    _KB_CACHE_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

_kb_cache_log = logging.getLogger('kb_cache')
_kb_cache_log.setLevel(logging.INFO)
if not _kb_cache_log.handlers:
    _h = logging.StreamHandler(sys.stderr)
    _h.setFormatter(logging.Formatter('[%(asctime)s] [KB-CACHE] %(message)s'))
    _kb_cache_log.addHandler(_h)


def _kb_cache_key(endpoint, params):
    """Stable hash across param order + value types."""
    canonical = '|'.join(
        f'{k}={v}' for k, v in sorted(params.items()))
    return hashlib.sha256(
        f'{endpoint}|{canonical}'.encode()).hexdigest()


def _kb_cache_get(key):
    path = _KB_CACHE_DIR / (key + '.pkl')
    try:
        st = path.stat()
    except FileNotFoundError:
        return None
    if time.time() - st.st_mtime > _KB_CACHE_TTL_SECS:
        return None
    try:
        with open(path, 'rb') as f:
            return pickle.load(f)
    except Exception:
        return None


def _kb_cache_set(key, value):
    path = _KB_CACHE_DIR / (key + '.pkl')
    tmp = path.with_suffix('.tmp')
    try:
        with open(tmp, 'wb') as f:
            pickle.dump(value, f)
        os.replace(tmp, path)
    except Exception:
        pass


def get_ids(locals_):
    params = {}
    for name in ['author_ids', 'affiliation_ids',
                 'conference_series_ids', 'journal_ids',
                 'field_of_study_ids', 'paper_ids']:
        ids = locals_[name]
        if ids:
            params[name.replace('_', '-')] = ','.join(map(str, ids))
    return params


class KonigsbergClient:
    def __init__(self, url):
        self.session = requests.Session()
        self.url = url

    def get_flower(
        self,
        *,
        author_ids=(),
        affiliation_ids=(),
        conference_series_ids=(),
        journal_ids=(),
        field_of_study_ids=(),
        paper_ids=(),
        pub_years=None,
        cit_years=None,
        coauthors=True,
        self_citations=False,
        max_results=None,
    ):
        params = {}
        params.update(get_ids(locals()))

        if self_citations:
            params['self-citations'] = 't'
        if not coauthors:
            params['exclude-coauthors'] = 't'

        if pub_years is not None:
            start_year, end_year = pub_years
            params['pub-years'] = f'{start_year},{end_year}'
        if cit_years is not None:
            start_year, end_year = cit_years
            params['cit-years'] = f'{start_year},{end_year}'

        if max_results is not None:
            params['max-results'] = str(max_results)

        cache_key = _kb_cache_key('get-flower', params)
        cached = _kb_cache_get(cache_key)
        if cached is not None:
            _kb_cache_log.info('HIT get-flower')
            return cached
        t0 = time.monotonic()
        response = self.session.get(self.url + '/get-flower', params=params)
        response.raise_for_status()
        result = response.json()
        _kb_cache_set(cache_key, result)
        _kb_cache_log.info(
            'STORE get-flower dt=%.1fs', time.monotonic() - t0)
        return result

    def get_stats(
        self,
        *,
        author_ids=(),
        affiliation_ids=(),
        conference_series_ids=(),
        journal_ids=(),
        field_of_study_ids=(),
        paper_ids=(),
    ):
        params = get_ids(locals())
        cache_key = _kb_cache_key('get-stats', params)
        cached = _kb_cache_get(cache_key)
        if cached is not None:
            _kb_cache_log.info('HIT get-stats')
            return cached
        t0 = time.monotonic()
        response = self.session.get(self.url + '/get-stats', params=params)
        response.raise_for_status()
        result = response.json()
        _kb_cache_set(cache_key, result)
        _kb_cache_log.info(
            'STORE get-stats dt=%.1fs', time.monotonic() - t0)
        return result

    def get_names(self, entity_type, ids):
        """Look up display names for the given OpenAlex ids.

        entity_type ∈ {'authors', 'institutions', 'sources', 'concepts'}.
        Returns {int_id: display_name}. Unknown ids are omitted.
        """
        if not ids:
            return {}
        response = self.session.get(
            self.url + '/get-names',
            params={'type': entity_type, 'ids': ','.join(map(str, ids))})
        response.raise_for_status()
        return {int(k): v for k, v in response.json().items()}

    def get_paper_info(self, paper_ids):
        """Look up title/year/venue for the given paper ids.

        Returns {int_id: {'title': str, 'year': int|None, 'venue': str}}.
        """
        if not paper_ids:
            return {}
        response = self.session.get(
            self.url + '/get-paper-info',
            params={'ids': ','.join(map(str, paper_ids))})
        response.raise_for_status()
        return {int(k): v for k, v in response.json().items()}

    def get_paper_citations(self, paper_ids):
        """Look up the citing papers for each given paper id.

        Returns {int_id: [citor_paper_id, ...]}.
        """
        if not paper_ids:
            return {}
        response = self.session.get(
            self.url + '/get-paper-citations',
            params={'ids': ','.join(map(str, paper_ids))})
        response.raise_for_status()
        return {int(k): [int(x) for x in v]
                for k, v in response.json().items()}

    def get_node_info(
        self,
        *,
        node_id=None,
        node_type=None,
        author_ids=(),
        affiliation_ids=(),
        conference_series_ids=(),
        journal_ids=(),
        field_of_study_ids=(),
        paper_ids=(),
        pub_years=None,
        cit_years=None,
        coauthors=True,
        self_citations=False,
        max_results=None,
    ):
        params = get_ids(locals())
        params.update({
            'node-id': int(node_id),
            'node-type': node_type
        })
        response = self.session.get(self.url + '/get-node-info', params=params)
        response.raise_for_status()
        return response.json()
