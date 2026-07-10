"""Fast one-pass, parallel generation of the three relation files.

Replaces the sequential trio in ``preprocessor.py``
(``generate_paper_references`` / ``generate_paper_authorships`` /
``generate_paper_fos``) which each full-scan the ~300 GB works snapshot
single-threaded — roughly a day PER FILE. This script:

- parses each works part-file ONCE, emitting all three outputs together
  (3 scans -> 1);
- fans part-files out to a process pool (N-way parallel gzip+JSON);
- writes plain CSV rows directly (no pandas);
- uses orjson when available (~5-10x faster than stdlib json).

Expected wall time on a multi-core data server: tens of minutes instead
of days.

Output files (same format as preprocessor.py, safe for builder.py):
- PaperReferences.txt        (citor_id,citee_id)
- PaperAuthorAffiliations.txt (paper_id,author_id,affiliation_id)
- PaperFieldsOfStudy.txt     (paper_id,fos_id)

Usage (on the data server):
    python konigsberg/fast_relations.py \\
        --data-dir /data_seoul/openalex/openalex-snapshot/data \\
        --workers 16
"""
import argparse
import gzip
import logging
import multiprocessing as mp
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

try:
    import orjson
    _loads = orjson.loads
except ImportError:
    import json
    _loads = json.loads

log = logging.getLogger('fast_relations')

PREFIX_WORK = "https://openalex.org/W"
PREFIX_AUTHOR = "https://openalex.org/A"
PREFIX_INST = "https://openalex.org/I"
PREFIX_FOS = "https://openalex.org/C"

_LW = len(PREFIX_WORK)
_LA = len(PREFIX_AUTHOR)
_LI = len(PREFIX_INST)
_LC = len(PREFIX_FOS)

# Pool globals (set once per worker via initializer; fork shares the
# merged-ids set copy-on-write so memory cost is paid once).
_MERGED = frozenset()
_SHARD_DIR = None


def _init_worker(merged_ids, shard_dir):
    global _MERGED, _SHARD_DIR
    _MERGED = merged_ids
    _SHARD_DIR = shard_dir


def _process_part(args):
    """Parse one part-file; write three shard outputs. Returns counts."""
    idx, part_path = args
    refs_path = Path(_SHARD_DIR) / f'refs.{idx:05d}'
    auth_path = Path(_SHARD_DIR) / f'auth.{idx:05d}'
    fos_path = Path(_SHARD_DIR) / f'fos.{idx:05d}'

    n_refs = n_auth = n_fos = 0
    refs_buf = []
    auth_buf = []
    fos_buf = []

    with gzip.open(part_path, 'rt', encoding='utf-8') as f:
        for line in f:
            try:
                d = _loads(line)
            except Exception:
                continue
            wid_url = d.get('id')
            if not wid_url:
                continue
            paper_id = wid_url[_LW:]
            if paper_id in _MERGED:
                continue

            # dict.fromkeys: dedupe while preserving order — OpenAlex
            # records can list the same reference/concept multiple
            # times inside one array, which multiplied every edge in
            # the bingraph.
            for rw in dict.fromkeys(d.get('referenced_works') or ()):
                if not rw:
                    continue
                citee = rw[_LW:]
                if citee in _MERGED:
                    continue
                refs_buf.append(f'{paper_id},{citee}\n')
                n_refs += 1

            seen_auth = set()
            for a in d.get('authorships') or ():
                author = (a.get('author') or {}).get('id')
                if not author:
                    continue
                author_id = author[_LA:]
                insts = [i['id'][_LI:] for i in (a.get('institutions') or ())
                         if i.get('id')] or ['']
                for inst in insts:
                    key = (author_id, inst)
                    if key in seen_auth:
                        continue
                    seen_auth.add(key)
                    auth_buf.append(f'{paper_id},{author_id},{inst}\n')
                    n_auth += 1

            seen_fos = set()
            for c in d.get('concepts') or ():
                level = c.get('level')
                if level is None or level > 1:
                    continue
                fid = c.get('id')
                if not fid:
                    continue
                fos_id = fid[_LC:]
                if fos_id in seen_fos:
                    continue
                seen_fos.add(fos_id)
                fos_buf.append(f'{paper_id},{fos_id}\n')
                n_fos += 1

    with open(refs_path, 'w') as f:
        f.writelines(refs_buf)
    with open(auth_path, 'w') as f:
        f.writelines(auth_buf)
    with open(fos_path, 'w') as f:
        f.writelines(fos_buf)
    return idx, n_refs, n_auth, n_fos


def _concat(shard_dir, pattern, outfile):
    """Concatenate shards (in index order) into the final file."""
    shards = sorted(Path(shard_dir).glob(pattern))
    log.info('concat %d shards -> %s', len(shards), outfile)
    with open(outfile, 'wb') as out:
        for shard in shards:
            with open(shard, 'rb') as f:
                shutil.copyfileobj(f, out, 1 << 24)
            shard.unlink()


def _load_merged_ids(data_path):
    """Merged work ids (same semantics as preprocessor.load_merged_ids)."""
    merged_dir = data_path / 'merged_ids' / 'works'
    ids = set()
    if not merged_dir.exists():
        return frozenset()
    import csv as _csv
    for fname in os.listdir(merged_dir):
        if not fname.endswith('.csv.gz'):
            continue
        with gzip.open(merged_dir / fname, 'rt') as f:
            reader = _csv.DictReader(f)
            for row in reader:
                rid = row.get('id', '')
                ids.add(rid.lstrip('W'))
    log.info('merged work ids: %d', len(ids))
    return frozenset(ids)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', required=True)
    parser.add_argument('--workers', type=int,
                        default=min(16, mp.cpu_count()))
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        stream=sys.stderr)

    data_path = Path(args.data_dir)
    part_files = sorted((data_path / 'works').glob(
        'updated_date=*/part_*.gz'))
    if not part_files:
        log.error('no part files under %s/works', data_path)
        sys.exit(1)
    log.info('%d part files, %d workers', len(part_files), args.workers)

    merged = _load_merged_ids(data_path)

    t0 = time.monotonic()
    with tempfile.TemporaryDirectory(dir=data_path,
                                     prefix='.relations_shards_') as shard_dir:
        tasks = list(enumerate(part_files))
        totals = [0, 0, 0]
        done = 0
        with mp.Pool(args.workers,
                     initializer=_init_worker,
                     initargs=(merged, shard_dir)) as pool:
            for idx, n_refs, n_auth, n_fos in pool.imap_unordered(
                    _process_part, tasks, chunksize=1):
                totals[0] += n_refs
                totals[1] += n_auth
                totals[2] += n_fos
                done += 1
                if done % 20 == 0 or done == len(tasks):
                    elapsed = time.monotonic() - t0
                    eta = elapsed / done * (len(tasks) - done)
                    log.info('%d/%d parts | refs=%d auth=%d fos=%d '
                             '| %.0fs elapsed, ETA %.0fs',
                             done, len(tasks), *totals, elapsed, eta)

        _concat(shard_dir, 'refs.*',
                data_path / 'PaperReferences.txt')
        _concat(shard_dir, 'auth.*',
                data_path / 'PaperAuthorAffiliations.txt')
        _concat(shard_dir, 'fos.*',
                data_path / 'PaperFieldsOfStudy.txt')

    # Record snapshot recency: the max updated_date partition IS the
    # snapshot date. builder.py copies this into the bingraph so
    # konigsberg /get-meta can report it (webapp shows "as of March
    # 2026" fully automatically).
    dates = sorted({p.parent.name.split('=', 1)[1]
                    for p in part_files
                    if '=' in p.parent.name})
    if dates:
        import json as _j
        meta_path = data_path / 'dataset-meta.json'
        with open(meta_path, 'w') as f:
            _j.dump({'snapshot_date': dates[-1]}, f)
        log.info('wrote %s (snapshot_date=%s)', meta_path, dates[-1])

    log.info('DONE in %.0fs: refs=%d auth=%d fos=%d',
             time.monotonic() - t0, *totals)


if __name__ == '__main__':
    main()
