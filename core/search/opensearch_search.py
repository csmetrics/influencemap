"""OpenSearch-backed search + paper-title lookup.

Replaces the old OpenAlex-API-based `core.search.query_info` module.
Public surface is intentionally compatible:

- ``query_entity_by_keyword(entity_types, keyword)`` — multi-index
  typeahead search across authors/institutions/sources/concepts/works.
  Returns ``list[tuple[entity_data_dict, entity_type_str]]``.
- ``fetch_paper_titles(paper_ids)`` — batch id -> title lookup against
  the works index. Used to enrich konigsberg's ``get_paper_info``
  response (title is not in the bingraph any more).
- ``convert_id(url_id, entity_type)`` — strip the OpenAlex URL prefix
  letter and return an int, e.g. ``"https://openalex.org/A123" -> 123``.
"""
import hashlib
import logging
import os
import pathlib
import pickle
import sys
import time

from opensearchpy import OpenSearch


# --- Response cache --------------------------------------------------------
#
# Cache msearch results per (types, keyword) so repeat searches for the
# same query skip OpenSearch entirely. Helps when konigsberg saturates
# disk I/O and Lucene reads queue up. TTL is short (a few hours) so new
# entities from the next snapshot naturally appear.

_OS_CACHE_DIR = pathlib.Path(
    os.getenv('OS_CACHE_DIR', '/influencemap/logs/os_cache'))
_OS_CACHE_TTL_SECS = int(
    os.getenv('OS_CACHE_TTL_SECS', str(6 * 3600)))
try:
    _OS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

_os_cache_log = logging.getLogger('os_cache')
_os_cache_log.setLevel(logging.INFO)
if not _os_cache_log.handlers:
    _h = logging.StreamHandler(sys.stderr)
    _h.setFormatter(logging.Formatter('[%(asctime)s] [OS-CACHE] %(message)s'))
    _os_cache_log.addHandler(_h)


def _os_cache_key(*parts):
    return hashlib.sha256('|'.join(map(str, parts)).encode()).hexdigest()


def _os_cache_get(key):
    path = _OS_CACHE_DIR / (key + '.pkl')
    try:
        st = path.stat()
    except FileNotFoundError:
        return None
    if time.time() - st.st_mtime > _OS_CACHE_TTL_SECS:
        return None
    try:
        with open(path, 'rb') as f:
            return pickle.load(f)
    except Exception:
        return None


def _os_cache_set(key, value):
    path = _OS_CACHE_DIR / (key + '.pkl')
    tmp = path.with_suffix('.tmp')
    try:
        with open(tmp, 'wb') as f:
            pickle.dump(value, f)
        os.replace(tmp, path)
    except Exception:
        pass


log = logging.getLogger(__name__)


_OPENSEARCH_URL = os.getenv('OPENSEARCH_URL', 'http://opensearch:9200')
# 30s covers force_merge/heavy-indexing periods where searches queue up.
# Under normal load queries return in <500ms; the ceiling is just to
# avoid failing when the cluster is temporarily busy.
_client = OpenSearch(
    hosts=[_OPENSEARCH_URL],
    http_compress=True,
    use_ssl=_OPENSEARCH_URL.startswith('https'),
    verify_certs=False,
    timeout=30,
    max_retries=1,
    retry_on_timeout=False,
)


# OpenAlex id URL prefixes.
_PREFIX = {
    'authors': 'A',
    'institutions': 'I',
    'sources': 'S',
    'concepts': 'C',
    'works': 'W',
}
_OPENALEX_URL = 'https://openalex.org/'


def convert_id(id_url, entity_type):
    """Strip the OpenAlex URL prefix and return the numeric id.

    ``convert_id("https://openalex.org/A123", "authors") -> 123``.
    Accepts both fully-qualified URL ids and bare ids.
    """
    letter = _PREFIX[entity_type]
    return int(str(id_url).split(letter)[-1])


# --- Multi-index search ----------------------------------------------------

# Default hits per index. Frontend paginates client-side; a few dozen per
# index is plenty for a typeahead selector.
_HITS_PER_INDEX = 20


def _search_fields(entity_type):
    """Which fields to run the typeahead bool_prefix query against."""
    base = 'title' if entity_type == 'works' else 'display_name'
    return [base, f'{base}._2gram', f'{base}._3gram']


def _tiebreaker(entity_type):
    """Sort secondary key: more-cited/more-productive entities first."""
    if entity_type == 'works':
        return 'cited_by_count'
    return 'works_count'


def _hit_to_entity_data(hit, entity_type):
    """Reshape an OpenSearch hit into the dict shape that ``webapp/views.py``
    ``/search`` expects (compatible with the old OpenAlex response).
    """
    src = hit.get('_source', {}) or {}
    entity_data = {
        'id': _OPENALEX_URL + _PREFIX[entity_type] + str(hit['_id']),
        # For works OpenSearch stores 'title'; for others 'display_name'.
        'display_name': src.get('display_name') or src.get('title', ''),
        'cited_by_count': src.get('cited_by_count', 0),
    }
    if entity_type != 'works':
        entity_data['works_count'] = src.get('works_count')
    if entity_type == 'concepts':
        entity_data['level'] = src.get('level')
    # 'affiliations' / 'authorships' — the old OpenAlex response included
    # these for extra display info. Not indexed locally; consumers already
    # guard with `if 'affiliations' in entity_data:` so leaving them out
    # is safe.
    return entity_data


def query_entity_by_keyword(entity_types, keyword):
    """Search each entity type in parallel; return ranked results.

    Return shape: ``list[(entity_data_dict, entity_type_str)]``, ordered
    per-index by score then tiebreaker. Cross-index ordering is
    per-index blocks in the order of ``entity_types``.
    """
    if not entity_types or not keyword:
        return []

    cache_key = _os_cache_key(
        'search', ','.join(sorted(entity_types)), keyword)
    cached = _os_cache_get(cache_key)
    if cached is not None:
        _os_cache_log.info('HIT search kw=%r', keyword[:40])
        return cached

    body = []
    for etype in entity_types:
        body.append({'index': etype})
        fields = _search_fields(etype)
        body.append({
            'query': {
                'multi_match': {
                    'query': keyword,
                    'type': 'bool_prefix',
                    'fields': fields,
                }
            },
            'sort': [
                {'_score': 'desc'},
                {_tiebreaker(etype): {'order': 'desc', 'missing': '_last'}},
            ],
            'size': _HITS_PER_INDEX,
        })

    try:
        response = _client.msearch(body=body)
    except Exception as e:
        log.warning('OpenSearch msearch failed: %s', e)
        return []

    results = []
    for etype, resp in zip(entity_types, response.get('responses', [])):
        if resp.get('error'):
            log.warning('OpenSearch %s query error: %s', etype, resp['error'])
            continue
        for hit in resp.get('hits', {}).get('hits', []):
            results.append((_hit_to_entity_data(hit, etype), etype))
    _os_cache_set(cache_key, results)
    _os_cache_log.info(
        'STORE search kw=%r hits=%d', keyword[:40], len(results))
    return results


# --- Paper title enrichment ------------------------------------------------

def fetch_paper_titles(paper_ids):
    """Batch id -> title lookup against the works index.

    Returns ``{int_id: title_str}``; ids not found are omitted.
    Called by ``core.search.local.papers_prop_query`` to fill in titles
    (which are no longer in konigsberg's bingraph).
    """
    if not paper_ids:
        return {}
    try:
        response = _client.mget(
            index='works',
            body={'ids': [str(pid) for pid in paper_ids]},
            _source=['title'],
        )
    except Exception as e:
        log.warning('OpenSearch mget titles failed: %s', e)
        return {}
    result = {}
    for doc in response.get('docs', []):
        if not doc.get('found'):
            continue
        title = (doc.get('_source') or {}).get('title')
        if title:
            try:
                result[int(doc['_id'])] = title
            except (TypeError, ValueError):
                pass
    return result
