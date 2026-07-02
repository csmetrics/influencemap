"""Local name/title lookups, backed by konigsberg + OpenSearch.

Drop-in replacement for the corresponding functions in the retired
``core.search.openalex`` and ``core.search.query_info`` modules. No
OpenAlex API calls. Public function names and return shapes match the
originals so callers can swap with a one-line import change.

- Display names for authors/institutions/sources/concepts come from
  konigsberg's ``/get-names`` (entity-name-*.bin mmap).
- Paper metadata: year + venue from konigsberg's ``/get-paper-info``;
  ``title`` from OpenSearch (paper-title-*.bin was retired to reclaim
  55 GB of page cache).
"""
import html
import os

import requests

from core.search.opensearch_search import fetch_paper_titles


_KONIGSBERG_URL = os.getenv('KONIGSBERG_URL', 'http://localhost:8081')
_session = requests.Session()


_HTTP_TIMEOUT = (5, 120)  # (connect_s, read_s)


def _fetch_names(entity_type, ids):
    """Call konigsberg /get-names. Returns {int_id: raw_name}."""
    if not ids:
        return {}
    response = _session.get(
        _KONIGSBERG_URL + '/get-names',
        params={
            'type': entity_type,
            'ids': ','.join(str(i) for i in ids),
        },
        timeout=_HTTP_TIMEOUT)
    response.raise_for_status()
    return {int(k): v for k, v in response.json().items()}


def _fetch_paper_info(ids):
    """Call konigsberg /get-paper-info.

    Returns ``{int_id: {'title': str, 'year': int|None, 'venue': str}}``.
    """
    if not ids:
        return {}
    response = _session.get(
        _KONIGSBERG_URL + '/get-paper-info',
        params={'ids': ','.join(str(i) for i in ids)},
        timeout=_HTTP_TIMEOUT)
    response.raise_for_status()
    return {int(k): v for k, v in response.json().items()}


def _names(entity_type, ids, with_id):
    """Look up names for `ids`, HTML-escaped to match openalex.py behavior.

    Returns a dict {id: escaped_name} when ``with_id`` is True, else the
    list of names in input order. Missing ids map to ``''`` so the caller's
    membership checks (``if id in ids_to_name``) still behave sensibly.
    """
    raw = _fetch_names(entity_type, ids)
    id_to_name = {
        int(eid): html.escape(raw.get(int(eid), '') or '', quote=True)
        for eid in ids
    }
    if with_id:
        return id_to_name
    return list(id_to_name.values())


# --- core/search/openalex.py public surface ---------------------------------

def get_names_from_conference_ids(entity_ids):
    return _names('sources', entity_ids, with_id=False)


def get_names_from_affiliation_ids(entity_ids, with_id=False):
    return _names('institutions', entity_ids, with_id=with_id)


def get_names_from_journal_ids(entity_ids):
    return _names('sources', entity_ids, with_id=False)


def get_display_names_from_conference_ids(entity_ids):
    return _names('sources', entity_ids, with_id=True)


def get_display_names_from_journal_ids(entity_ids):
    return _names('sources', entity_ids, with_id=True)


def get_display_names_from_author_ids(entity_ids, with_id=False):
    return _names('authors', entity_ids, with_id=with_id)


def get_display_names_from_fos_ids(entity_ids, with_id=False):
    return _names('concepts', entity_ids, with_id=with_id)


# --- core/search/query_info.py public surface (partial) ---------------------

# OpenAlex entity-type strings used by views.py:268-277. 'works' is handled
# separately because the konigsberg endpoint differs.
_KONIGSBERG_TYPE = {
    'authors': 'authors',
    'institutions': 'institutions',
    'sources': 'sources',
    'concepts': 'concepts',
}


def query_entity_by_id(entity_type, entity_id):
    """Return the display name (or title, for works) of a single entity.

    Returns ``''`` if the id is unknown locally.
    """
    if entity_type == 'works':
        info = _fetch_paper_info([entity_id])
        rec = info.get(int(entity_id))
        return rec['title'] if rec else ''
    konigsberg_type = _KONIGSBERG_TYPE.get(entity_type)
    if konigsberg_type is None:
        return ''
    names = _fetch_names(konigsberg_type, [entity_id])
    return names.get(int(entity_id), '')


def papers_prop_query(paper_ids):
    """Return {paper_id: {'PaperId', 'OriginalTitle', 'OriginalVenue', 'Year'}}.

    Matches the dict shape of the retired ``core.search.query_info``
    ``papers_prop_query``. Year + venue come from konigsberg (via graph
    walk); title comes from OpenSearch.
    """
    info = _fetch_paper_info(paper_ids)
    if not info:
        return {}
    titles = fetch_paper_titles(list(info.keys()))
    return {
        pid: {
            'PaperId': pid,
            'OriginalTitle': titles.get(pid) or rec.get('title', ''),
            'OriginalVenue': rec.get('venue', ''),
            'Year': rec.get('year'),
        }
        for pid, rec in info.items()
    }
