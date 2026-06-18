"""Build id-to-name binary files from CSV inputs.

Run this after ``builder.py`` finishes. Produces, in the bingraph directory:

- ``entity-name-ptr.bin`` (uint64, length N_entities + 1)
  ``entity-name-dat.bin`` (uint8 UTF-8 bytes)

  Display names for authors + institutions + concepts + sources, concatenated
  in the same order as ``entities-ind2id.bin`` (the unified entity index
  established by ``builder.py``).

- ``paper-title-ptr.bin`` (uint64, length N_papers + 1)
  ``paper-title-dat.bin`` (uint8 UTF-8 bytes)

  Paper titles, in the order of ``paper-ind2id.bin``.

Lookup pattern (variable-length CSR):

    start = ptr[i]; end = ptr[i + 1]
    name = bytes(dat[start:end]).decode('utf-8')

CLI:

    # Run from the konigsberg/ directory (matches builder.py convention):
    python id2name_builder.py \\
        --csv-dir /data_seoul/openalex/openalex-snapshot/data \\
        --bingraph bingraph-openalex

    # Or as a module from the repo root:
    python -m konigsberg.id2name_builder --csv-dir ... --bingraph ...
"""
import argparse
import csv
import json
import logging
import mmap
import pathlib

import numpy as np
import pandas as pd

try:
    from . import hashutil
except ImportError:  # Allow `python id2name_builder.py` from konigsberg/.
    import hashutil

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class OpenAlexDialect(csv.Dialect):
    """Tab-delimited, QUOTE_NONE. Mirrors preprocessor.OpenAlexDialect.

    Safe because preprocessor sanitizes display names/titles (replaces tab,
    CR, LF with single space).
    """
    delimiter = '\t'
    doublequote = False
    escapechar = None
    lineterminator = '\r\n'
    quotechar = None
    quoting = csv.QUOTE_NONE
    skipinitialspace = False
    strict = True


# Entity type ordering MUST match builder.py:make_dataset entity_infos.
# Each tuple is (txt filename stem, entity-counts.json key).
ENTITY_TYPES = [
    ('authors', 'authors'),
    ('institutions', 'aff'),
    ('concepts', 'fos'),
    ('sources', 'journals'),
]


def _load_entity_id_to_name(csv_path):
    """Load id -> display_name from an entity txt file into a dict."""
    df = pd.read_csv(
        csv_path,
        header=0,
        dialect=OpenAlexDialect(),
        engine='c',
        na_filter=False,
        usecols=['id', 'display_name'],
        dtype={'id': np.uint64, 'display_name': object},
    )
    return dict(zip(df['id'].to_numpy(), df['display_name'].astype(str)))


def build_entity_names(in_dir, out_dir):
    """Build entity-name-ptr.bin and entity-name-dat.bin."""
    in_dir = pathlib.Path(in_dir)
    out_dir = pathlib.Path(out_dir)

    with open(out_dir / 'entity-counts.json') as f:
        counts = json.load(f)

    ind2id = np.memmap(out_dir / 'entities-ind2id.bin',
                       dtype=np.uint64, mode='r')

    total = sum(counts[k] for _, k in ENTITY_TYPES)
    if len(ind2id) != total:
        raise ValueError(
            f'entities-ind2id.bin has {len(ind2id)} entries but '
            f'entity-counts.json sums to {total}')

    # ptr fits comfortably in memory: 8 bytes * (N+1).
    # ~800MB for 100M entities on a 125GB server.
    ptr = np.empty(total + 1, dtype=np.uint64)
    ptr[0] = 0

    dat_path = out_dir / 'entity-name-dat.bin'
    cursor = 0
    offset = 0
    with open(dat_path, 'wb') as dat_f:
        for type_stem, count_key in ENTITY_TYPES:
            n = counts[count_key]
            logger.info('...loading id->name dict for %s (%d entries)',
                        type_stem, n)
            id_to_name = _load_entity_id_to_name(in_dir / (type_stem + '.txt'))

            logger.info('...writing names for %s', type_stem)
            missing = 0
            for i in range(n):
                eid = int(ind2id[cursor + i])
                name = id_to_name.get(eid)
                if name is None:
                    name = ''
                    missing += 1
                name_bytes = name.encode('utf-8')
                if name_bytes:
                    dat_f.write(name_bytes)
                offset += len(name_bytes)
                ptr[cursor + i + 1] = offset

            if missing:
                logger.warning('...%s: %d ids in ind2id not in %s.txt',
                               type_stem, missing, type_stem)
            cursor += n
            del id_to_name  # Free before next type.

    ptr.tofile(out_dir / 'entity-name-ptr.bin')
    logger.info('done: entity-name-* (%d entries, %d dat bytes)',
                total, offset)


def _stream_works_chunks(works_path, chunksize):
    """Yield (paper_id_array, title_array) chunks from works.txt.

    paper_id is uint64. title is Python str (may be empty).
    """
    for chunk in pd.read_csv(
        works_path,
        header=0,
        dialect=OpenAlexDialect(),
        engine='c',
        na_filter=False,
        usecols=['paper_id', 'title'],
        dtype={'paper_id': np.uint64, 'title': object},
        chunksize=chunksize,
    ):
        # Some rows may have an empty title; coerce NaN-or-missing to ''.
        titles = chunk['title'].fillna('').astype(str).to_numpy()
        yield chunk, titles


def build_paper_titles(in_dir, out_dir, chunksize=1_000_000):
    """Two-pass build of paper-title-{ptr,dat}.bin from works.txt.

    Pass 1: stream works.txt; for each paper_id resolve its index via the
    existing id2ind hash map; accumulate UTF-8 byte lengths in a uint64
    array. Convert lengths -> cumulative offsets to form ptr.

    Pass 2: stream works.txt again; mmap the pre-sized dat file; write
    title bytes at their ptr offsets. Random writes; the OS handles
    page-cache scheduling.

    Total runtime is dominated by the 500M-row CSV reads. On NVMe with a
    big-enough page cache, expect a few hours per pass.
    """
    in_dir = pathlib.Path(in_dir)
    out_dir = pathlib.Path(out_dir)
    works_path = in_dir / 'works.txt'

    ind2id_map = hashutil.Ind2IdMap(out_dir / 'paper-ind2id.bin')
    n_papers = len(ind2id_map.ind2id)
    logger.info('papers: %d', n_papers)

    # Pass 1: lengths.
    logger.info('pass 1: computing title lengths')
    lengths = np.zeros(n_papers, dtype=np.uint64)
    n_rows = 0
    id2ind_map = hashutil.Id2IndHashMap(
        out_dir / 'paper-id2ind.bin', ind2id_map)
    with id2ind_map:
        for chunk, titles in _stream_works_chunks(works_path, chunksize):
            id2ind_map.convert_inplace(chunk, 'paper_id', allow_missing=True)
            inds = chunk['paper_id'].to_numpy()
            valid = inds != hashutil.SENTINEL
            for ind, title in zip(inds[valid], titles[valid]):
                lengths[ind] = len(title.encode('utf-8'))
            n_rows += len(chunk)
            if n_rows % (chunksize * 10) == 0:
                logger.info('  ...%d rows processed', n_rows)

    ptr = np.empty(n_papers + 1, dtype=np.uint64)
    ptr[0] = 0
    np.cumsum(lengths, dtype=np.uint64, out=ptr[1:])
    total_size = int(ptr[-1])
    del lengths
    logger.info('total title bytes: %d', total_size)

    ptr.tofile(out_dir / 'paper-title-ptr.bin')

    # Pre-allocate dat file.
    dat_path = out_dir / 'paper-title-dat.bin'
    with open(dat_path, 'wb') as f:
        if total_size > 0:
            f.seek(total_size - 1)
            f.write(b'\x00')

    if total_size == 0:
        logger.info('done: paper-title-* (no titles)')
        return

    # Pass 2: write titles at offsets via mmap.
    logger.info('pass 2: writing titles')
    # Re-open the hash map (the with-block above closed it).
    ind2id_map_2 = hashutil.Ind2IdMap(out_dir / 'paper-ind2id.bin')
    id2ind_map_2 = hashutil.Id2IndHashMap(
        out_dir / 'paper-id2ind.bin', ind2id_map_2)

    n_rows = 0
    with id2ind_map_2, open(dat_path, 'r+b') as dat_f:
        dat_mmap = mmap.mmap(dat_f.fileno(), total_size)
        try:
            for chunk, titles in _stream_works_chunks(works_path, chunksize):
                id2ind_map_2.convert_inplace(
                    chunk, 'paper_id', allow_missing=True)
                inds = chunk['paper_id'].to_numpy()
                valid = inds != hashutil.SENTINEL
                for ind, title in zip(inds[valid], titles[valid]):
                    start = int(ptr[ind])
                    end = int(ptr[ind + 1])
                    if end > start:
                        dat_mmap[start:end] = title.encode('utf-8')
                n_rows += len(chunk)
                if n_rows % (chunksize * 10) == 0:
                    logger.info('  ...%d rows written', n_rows)
        finally:
            dat_mmap.flush()
            dat_mmap.close()

    logger.info('done: paper-title-* (%d entries, %d dat bytes)',
                n_papers, total_size)


def main():
    parser = argparse.ArgumentParser(
        description='Build id-to-name binary files from CSV inputs.')
    parser.add_argument(
        '--csv-dir', required=True,
        help='Directory containing authors.txt, institutions.txt, '
             'concepts.txt, sources.txt, works.txt.')
    parser.add_argument(
        '--bingraph', required=True,
        help='Existing bingraph directory (output of builder.py). '
             'New files are written here.')
    parser.add_argument(
        '--skip-entities', action='store_true',
        help='Skip entity-name-* build.')
    parser.add_argument(
        '--skip-papers', action='store_true',
        help='Skip paper-title-* build.')
    parser.add_argument(
        '--chunksize', type=int, default=1_000_000,
        help='pd.read_csv chunksize for works.txt (default: 1,000,000).')
    args = parser.parse_args()

    stream_handler = logging.StreamHandler()
    logger.addHandler(stream_handler)
    try:
        if not args.skip_entities:
            build_entity_names(args.csv_dir, args.bingraph)
        if not args.skip_papers:
            build_paper_titles(
                args.csv_dir, args.bingraph, chunksize=args.chunksize)
    finally:
        logger.removeHandler(stream_handler)


if __name__ == '__main__':
    main()
