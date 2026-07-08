"""Index OpenAlex snapshot CSVs into OpenSearch.

Reads the ``.txt`` files produced by ``konigsberg.preprocessor`` and
pushes them into per-entity OpenSearch indexes. Uses versioned index
names plus an alias swap so a re-index is zero-downtime.

Index layout:

- ``authors``         (~95M docs)  -> display_name, works_count
- ``institutions``    (~110K docs) -> display_name, works_count, country_code, ror
- ``sources``         (~250K docs) -> display_name, works_count, type, issn_l
- ``concepts``        (~65K docs)  -> display_name, works_count, level
- ``works``           (~500M docs) -> title, year, venue_display_name, cited_by_count

``display_name`` and ``title`` use OpenSearch's ``search_as_you_type``
field, which auto-generates 2/3-gram subfields for prefix (typeahead)
matches.

Usage:

    # Index everything (multi-hour run for works):
    python -m scripts.index_to_opensearch \\
        --url http://opensearch:9200 \\
        --data-dir /data/openalex-snapshot/data

    # Just one entity type (e.g. rebuild authors):
    python -m scripts.index_to_opensearch \\
        --url http://opensearch:9200 \\
        --data-dir /data/openalex-snapshot/data \\
        --entity authors

    # Drop the currently-aliased index before re-indexing:
    python -m scripts.index_to_opensearch --recreate ...
"""
import argparse
import csv
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from opensearchpy import OpenSearch, helpers


log = logging.getLogger('index_to_opensearch')


# --- Per-entity config ------------------------------------------------------

# Preprocessor uses this dialect for all entity + works files.
_TSV_KW = dict(delimiter='\t', quoting=csv.QUOTE_NONE, quotechar=None,
               escapechar=None)


ENTITY_CONFIG = {
    'authors': {
        'csv_name': 'authors.txt',
        'columns': ['id', 'works_count', 'display_name', 'affiliations'],
        'id_field': 'id',
        'shards': 4,
    },
    'institutions': {
        'csv_name': 'institutions.txt',
        'columns': ['id', 'works_count', 'display_name',
                    'country_code', 'ror', 'acronyms',
                    'alternatives', 'cited_by_count'],
        'id_field': 'id',
        'shards': 1,
    },
    'sources': {
        'csv_name': 'sources.txt',
        'columns': ['id', 'works_count', 'display_name',
                    'type', 'issn_l'],
        'id_field': 'id',
        'shards': 1,
    },
    'concepts': {
        'csv_name': 'concepts.txt',
        'columns': ['id', 'works_count', 'display_name', 'level'],
        'id_field': 'id',
        'shards': 1,
    },
    'works': {
        'csv_name': 'works.txt',
        'columns': ['paper_id', 'rank', 'year', 'journal_id',
                    'title', 'venue_display_name'],
        'id_field': 'paper_id',
        'shards': 12,
    },
}


# Estimated total docs per entity (used for progress logging only).
ROW_ESTIMATES = {
    'authors': 95_000_000,
    'institutions': 110_000,
    'sources': 250_000,
    'concepts': 65_000,
    'works': 500_000_000,
}


def _mapping_for(entity_type):
    """Build the index mapping + settings dict for `entity_type`."""
    conf = ENTITY_CONFIG[entity_type]

    if entity_type == 'works':
        properties = {
            'title': {
                'type': 'search_as_you_type',
                'max_shingle_size': 3,
            },
            'year': {'type': 'integer'},
            'journal_id': {'type': 'keyword'},
            'venue_display_name': {
                'type': 'keyword',
                'fields': {'text': {'type': 'text'}},
            },
            'cited_by_count': {'type': 'integer'},
        }
    else:
        properties = {
            'display_name': {
                'type': 'search_as_you_type',
                'max_shingle_size': 3,
                'fields': {'keyword': {'type': 'keyword'}},
            },
            'works_count': {'type': 'integer'},
        }
        if entity_type == 'authors':
            # Pipe-separated last_known_institutions display names, kept
            # as a single text blob so the frontend can show them
            # without requiring a nested mapping.
            properties['affiliations'] = {'type': 'text'}
        elif entity_type == 'institutions':
            properties['country_code'] = {'type': 'keyword'}
            properties['ror'] = {'type': 'keyword'}
            # search_as_you_type so bool_prefix typeahead matches
            # acronyms ("ANU") and alternative names ("The Australian
            # National University") the same way it matches names.
            properties['acronyms'] = {
                'type': 'search_as_you_type',
                'max_shingle_size': 3,
            }
            properties['alternatives'] = {
                'type': 'search_as_you_type',
                'max_shingle_size': 3,
            }
            properties['cited_by_count'] = {'type': 'integer'}
        elif entity_type == 'sources':
            properties['type'] = {'type': 'keyword'}
            properties['issn_l'] = {'type': 'keyword'}
        elif entity_type == 'concepts':
            properties['level'] = {'type': 'integer'}

    return {
        'mappings': {'properties': properties},
        'settings': {
            'number_of_shards': conf['shards'],
            'number_of_replicas': 0,
            # Bulk-friendly: no near-real-time. Flipped to 1s post-index.
            'refresh_interval': '-1',
            'index': {
                'translog': {'durability': 'async', 'sync_interval': '30s'},
            },
        },
    }


# --- Doc streaming ----------------------------------------------------------

def _int_or_none(v):
    if v is None or v == '':
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _stream_docs(csv_path, entity_type, index_name):
    """Yield bulk-action dicts, one per row."""
    conf = ENTITY_CONFIG[entity_type]
    id_field = conf['id_field']

    with open(csv_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f, fieldnames=None, **_TSV_KW)
        for row in reader:
            eid = row.get(id_field)
            if not eid:
                continue

            if entity_type == 'works':
                source = {}
                title = row.get('title') or ''
                if title:
                    source['title'] = title
                year = _int_or_none(row.get('year'))
                if year is not None and 1500 <= year <= 2200:
                    source['year'] = year
                venue = row.get('venue_display_name') or ''
                if venue:
                    source['venue_display_name'] = venue
                jid = row.get('journal_id')
                if jid:
                    source['journal_id'] = jid
                cbc = _int_or_none(row.get('rank'))
                if cbc is not None:
                    source['cited_by_count'] = cbc
            else:
                source = {}
                name = row.get('display_name') or ''
                if name:
                    source['display_name'] = name
                wc = _int_or_none(row.get('works_count'))
                if wc is not None:
                    source['works_count'] = wc
                for extra in ('country_code', 'ror', 'type',
                              'issn_l', 'level', 'affiliations',
                              'acronyms', 'alternatives',
                              'cited_by_count'):
                    val = row.get(extra)
                    if val:
                        if extra in ('level', 'cited_by_count'):
                            v = _int_or_none(val)
                            if v is not None:
                                source[extra] = v
                        else:
                            source[extra] = val

            yield {
                '_op_type': 'index',
                '_index': index_name,
                '_id': eid,
                '_source': source,
            }


# --- Index lifecycle --------------------------------------------------------

def _new_versioned_name(entity_type):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    return f'{entity_type}_v{stamp}'


def _create_index(client, entity_type, index_name):
    body = _mapping_for(entity_type)
    log.info('creating %s (shards=%d)', index_name,
             body['settings']['number_of_shards'])
    client.indices.create(index=index_name, body=body)


def _finalize_index(client, index_name):
    """Post-bulk: flip refresh, refresh, kick off async force_merge.

    force_merge is a background query-performance optimization that can
    take many hours on multi-hundred-million-doc indexes. We fire it
    with wait_for_completion=false so the indexer script can proceed to
    the alias swap immediately; OpenSearch keeps merging in the
    background. Check status later via
    ``GET _tasks?actions=*forcemerge*``.
    """
    log.info('finalizing %s: refresh_interval=1s + refresh', index_name)
    client.indices.put_settings(
        index=index_name,
        body={'index': {'refresh_interval': '1s'}})
    client.indices.refresh(index=index_name)
    try:
        client.indices.forcemerge(
            index=index_name, max_num_segments=5,
            params={'wait_for_completion': 'false'})
        log.info('force_merge submitted asynchronously; check '
                 'GET _tasks?actions=*forcemerge* for progress')
    except Exception as e:
        log.warning('force_merge submission failed (non-fatal): %s', e)


def _swap_alias(client, alias, new_index, delete_old=False):
    """Point `alias` at `new_index`, remove from any others."""
    try:
        existing = client.indices.get_alias(name=alias)
    except Exception:
        existing = {}

    actions = []
    for old_index in existing:
        if old_index != new_index:
            actions.append({'remove': {'index': old_index, 'alias': alias}})
    actions.append({'add': {'index': new_index, 'alias': alias}})
    log.info('swapping alias %s: %s', alias, actions)
    client.indices.update_aliases(body={'actions': actions})

    if delete_old:
        for old_index in existing:
            if old_index != new_index:
                log.info('deleting old index %s', old_index)
                try:
                    client.indices.delete(index=old_index)
                except Exception as e:
                    log.warning('delete failed: %s', e)


# --- Main index driver ------------------------------------------------------

def index_entity(client, entity_type, data_dir,
                 *, chunk_size, recreate, delete_old):
    conf = ENTITY_CONFIG[entity_type]
    csv_path = Path(data_dir) / conf['csv_name']
    if not csv_path.exists():
        log.error('missing %s (skipping %s)', csv_path, entity_type)
        return 0, 0

    alias = entity_type
    if recreate:
        try:
            existing = client.indices.get_alias(name=alias)
            for name in list(existing):
                log.info('recreate: deleting %s', name)
                client.indices.delete(index=name)
        except Exception:
            pass

    new_index = _new_versioned_name(entity_type)
    _create_index(client, entity_type, new_index)

    estimate = ROW_ESTIMATES.get(entity_type, 0)
    log.info('bulk indexing %s -> %s (~%d rows)',
             csv_path.name, new_index, estimate)

    n_ok = 0
    n_fail = 0
    t0 = time.monotonic()
    last_log = t0
    LOG_EVERY_S = 30

    docs = _stream_docs(csv_path, entity_type, new_index)
    for ok, item in helpers.streaming_bulk(
            client, docs,
            chunk_size=chunk_size,
            max_chunk_bytes=100 * 1024 * 1024,
            request_timeout=120,
            raise_on_error=False,
            raise_on_exception=False):
        if ok:
            n_ok += 1
        else:
            n_fail += 1
            if n_fail <= 10:
                log.warning('bulk item failed: %s', item)
        now = time.monotonic()
        if now - last_log >= LOG_EVERY_S:
            elapsed = now - t0
            rate = (n_ok + n_fail) / max(elapsed, 1)
            eta_s = (estimate - n_ok - n_fail) / max(rate, 1) if estimate else -1
            log.info(
                '%s: %d ok / %d fail | %.0f docs/s | %.0fs elapsed | ETA %.0fs',
                entity_type, n_ok, n_fail, rate, elapsed, eta_s)
            last_log = now

    log.info('%s: bulk done: %d ok / %d fail in %.1fs',
             entity_type, n_ok, n_fail, time.monotonic() - t0)

    _finalize_index(client, new_index)
    _swap_alias(client, alias, new_index, delete_old=delete_old)
    return n_ok, n_fail


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--url', required=True,
        help='OpenSearch base URL, e.g. http://opensearch:9200')
    parser.add_argument(
        '--data-dir', required=True,
        help='Directory containing authors.txt, works.txt, etc.')
    parser.add_argument(
        '--entity', choices=list(ENTITY_CONFIG) + ['all'], default='all',
        help='Which entity type to index (default: all)')
    parser.add_argument(
        '--chunk-size', type=int, default=5000,
        help='Bulk chunk size (default 5000; smaller for slow network)')
    parser.add_argument(
        '--recreate', action='store_true',
        help='Delete existing aliased index for this entity first.')
    parser.add_argument(
        '--delete-old', action='store_true',
        help='After alias swap, delete previously-aliased indexes.')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        stream=sys.stderr)

    client = OpenSearch(
        hosts=[args.url],
        http_compress=True,
        use_ssl=args.url.startswith('https'),
        verify_certs=False,
        timeout=60,
        max_retries=3,
        retry_on_timeout=True)

    # Sanity check
    info = client.info()
    log.info('connected: cluster=%s version=%s',
             info.get('cluster_name'), info.get('version', {}).get('number'))

    entities = [args.entity] if args.entity != 'all' else list(ENTITY_CONFIG)
    total_ok = total_fail = 0
    for etype in entities:
        try:
            ok, fail = index_entity(
                client, etype, args.data_dir,
                chunk_size=args.chunk_size,
                recreate=args.recreate,
                delete_old=args.delete_old)
            total_ok += ok
            total_fail += fail
        except Exception as e:
            log.exception('index_entity %s failed: %s', etype, e)
            total_fail += 1

    log.info('DONE: %d ok, %d fail', total_ok, total_fail)
    if total_fail:
        sys.exit(1)


if __name__ == '__main__':
    main()
