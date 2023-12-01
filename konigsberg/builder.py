import csv
import json
import logging
import pathlib

import numpy as np
import pandas as pd

import hashutil
import sparseutil

YEAR_SENTINEL = np.uint16(-1)  # Denotes missing year
INDEX_SENTINEL = np.uint32(-1)  # Denotes deleted entity

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class OpenAlexDialect(csv.Dialect):
    """Open Alex Graph table file format."""
    delimiter = '\t'
    doublequote = False
    escapechar = None
    lineterminator = '\r\n'
    quotechar = None
    quoting = csv.QUOTE_NONE
    skipinitialspace = False
    strict = True


def load_entity_df(path, meta_func=None, filter_column=None, sort_column=None):
    """Load a table listing non-paper entities.

    Non-paper entities are authors, affiliations, journals, conference
    series, and fields of study.

    The table is a file at `path` in the MAG format. The first two
    columns are read: the first is assumed to be the entity id (an
    integer in {0, ..., 2^32 - 1}), which is returned; the second is the
    rank (in {0, ..., 2^16 - 1}), which is used for sorting.

    The optional filter_column argument permits filtering on a column.
    If passed, it must be a 4-tuple of column index, column name,
    column dtype, and filter function. The filter function takes the
    filter column (now as filter series) and returns a mask of the rows
    to keep. The filter series is not returned. As an example, to filter
    fields of study so that only fields with level <= 1 are kept, we use
    filter_column = (5, 'level', np.uint8, lambda level: level <= 1).
    The level is at index 5 in the table, fits within a np.uint8, and
    level <= 1 yields the mask when given the series of levels.

    OpenAlex update:
    OpenAlex ID is an url, e.g., `https://openalex.org/A2283863768`.
    The last part of the url consists of one alphabet (indicating entity type)
    and a number, such as `A2283863768`. Only number `2283863768` is used.
    Entity id range for OpenAlex changes to {0, ..., 2^64 - 1})
    """
    indices = [0, 1]
    names = ['id', 'rank']
    dtypes = {'id': np.uint64, 'rank': np.uint16}
    if filter_column:
        filter_col_i, filter_col_name, filter_col_dtype, _ = filter_column
        indices.append(filter_col_i)
        names.append(filter_col_name)
        dtypes[filter_col_name] = filter_col_dtype
    df = pd.read_csv(
        path, header=1,
        dialect=OpenAlexDialect(), engine='c', na_filter=False,
        usecols=indices, names=names, dtype=dtypes)
    meta = None if meta_func is None else meta_func(df)
    if sort_column:
        df.sort_values(
            sort_column, inplace=True, ignore_index=True, kind='mergesort')
    if filter_column:
        _, filter_col_name, _, filter_f = filter_column
        df = df[filter_f(df[filter_col_name])]
        df.reset_index(drop=True, inplace=True)  # Save memory.
        del df[filter_col_name]
    df.sort_values('rank', inplace=True, ignore_index=True, kind='mergesort')
    del df['rank']
    return df, meta


IN_SUFF = '.txt'
ID2IND_SUFF = '-id2ind.bin'
META_SUFF = '-meta.json'


def process_entity_listings(in_dir, out_dir, out_fname_ind2id, entity_infos):
    """Load entity tables and make ID-index mappings.

    This function takes multiple entity tables and assigns them
    consecutive indices.

    ### caution: below docs are slightly out of date
    entity_path is an iterable of 3-tuples: path to table (read), path
    to the ID-to-index map (written), and an optional row filter (see 
    `load_entity_df`). out_path_ind2id is the path to the index-to-ID
    map (written). Note that while one ID-to-index map is produced per
    table, only one index-to-ID map is produced for all tables; this is
    because the indices are consecutive.

    Returns a list of ID-to-index maps, as well a list of the number of
    entities per table.
    """
    in_dir = pathlib.Path(in_dir)
    out_dir = pathlib.Path(out_dir)
    counts = []
    with open(out_dir / out_fname_ind2id, 'wb') as ind_to_id_f:
        offset = 0
        for in_fname, out_fname, meta_info, filter_info, sort_info \
                in entity_infos:
            df, meta = load_entity_df(
                in_dir / (in_fname + IN_SUFF),
                meta_info, filter_info, sort_info)
            id_arr = df['id'].to_numpy()
            ind_to_id_f.write(id_arr)  # Index to ID: copy array of IDS.
            hashutil.make_id_hash_map(
                id_arr, out_dir / (out_fname + ID2IND_SUFF), offset)
            count = len(df)
            counts.append(count)
            offset += count
            if meta is not None:
                with open(out_dir / (out_fname + META_SUFF), 'w') as meta_f:
                    json.dump(meta, meta_f)

    ind2id_map = hashutil.Ind2IdMap(out_dir / out_fname_ind2id)
    id2ind_maps = tuple(
        hashutil.Id2IndHashMap(out_dir / (path + ID2IND_SUFF), ind2id_map)
        for _, path, _, _, _ in entity_infos)
    return id2ind_maps, counts


def load_papers_df(path):
    """Load table listing papers.

    The table is in MAG format at `path`.

    Returns:
    1. a DataFrame of all paper IDs,
    2. a DataFrame of paper, journal ID, where the Journal ID exists,
    3. a DataFrame of paper, conference series ID, where exists.

    The papers are sorted by year. Within each year, they are sorted by
    rank.
    """
    df = pd.read_csv(
        path, header=1,
        dialect=OpenAlexDialect(), engine='c',
        usecols=[0, 1, 2, 3],
        names=['paper_id', 'rank', 'year', 'journal_id'],
        dtype={'paper_id': np.uint64, 'rank': np.uint16,
               'year': pd.UInt16Dtype(), 'journal_id': pd.UInt64Dtype()},
        keep_default_na=False,
        na_values={'year': [''], 'journal_id': ['']})

    # Make separate tables for paper-journal/conference series mappings.
    paper_journals_df = df.loc[df['journal_id'].notna(),
                               ['paper_id', 'journal_id']]
    paper_journals_df.reset_index(drop=True, inplace=True)  # Memory.
    paper_journals_df['journal_id'] \
        = paper_journals_df['journal_id'].astype(np.uint64)
    del df['journal_id']

    df['year'].fillna(YEAR_SENTINEL, inplace=True)  # NaN -> sentinel.
    df['year'] = df['year'].astype(np.uint16)  # From masked type.
    # 'mergesort' is stable, unlike the other sorts. Remember that we
    # want to sort by year, then rank.
    df.sort_values('rank', inplace=True, ignore_index=True, kind='mergesort')
    del df['rank']
    df.sort_values('year', inplace=True, ignore_index=True, kind='mergesort')

    return df, paper_journals_df


def load_authorships_df(path):
    """Load table of authorships and affiliations.

    The table is at `path` in the MAG format. The first three columns
    are used; these are the paper ID, author ID, and affiliation ID (or
    blank).

    Returns:
    1. a DataFrame of paper IDs and the corresponding author IDs,
    2. a DataFrame of paper IDs and the corresponding affiliation IDs.

    Duplicate entries are permitted. Null affiliations are not returned.
    """
    df = pd.read_csv(
        path,
        engine='c',
        usecols=[0, 1, 2], names=['paper_id', 'author_id', 'affiliation_id'],
        dtype={'paper_id': np.uint64, 'author_id': np.uint64,
               'affiliation_id': pd.UInt64Dtype()},
        keep_default_na=False, na_values={'affiliation_id': ['']})

    paper_affiliations_df = df.loc[df['affiliation_id'].notna(),
                                   ['paper_id', 'affiliation_id']]
    paper_affiliations_df.reset_index(drop=True, inplace=True)
    paper_affiliations_df['affiliation_id'] \
        = paper_affiliations_df['affiliation_id'].astype(np.uint64)
    del df['affiliation_id']
    return df, paper_affiliations_df


def load_many_to_many_mapping(path, colname1, colname2):
    """Load table representing a many-to-many mapping.

    Examples of many-to-many mappings are references, authorships, and
    paper fields of study.

    The table is at `path` in the MAG format. The first two columns are
    used. The values must fit in {0, ..., 2^64 - 1}. `colname1` and
    `colname2` are the names of the columns at indices 0 and 1,
    respectively.

    Returns a DataFrame with columns `colname1` and `colname2`.
    """
    return pd.read_csv(
        path,
        engine='c', na_filter=False,
        usecols=[0, 1], names=[colname1, colname2],
        dtype={colname1: np.uint64, colname2: np.uint64})


def load_citations_df(path):
    """Load table of citations."""
    return load_many_to_many_mapping(path, 'citor_id', 'citee_id')


def load_paper_fos_df(path):
    """Load table of paper fields of study."""
    return load_many_to_many_mapping(path, 'paper_id', 'fos_id')


def save_paper_years(df, path):
    """Save paper index range per year as in a JSON file.

    The papers are sorted chronologically to permit filtering by year.
    This function finds the lowest index for a particular year and saves
    it in a JSON file. The entire range of indices for year y is
    {years_dict[y], ..., years_dict[y + 1] - 1}.
    """
    # Find smallest index greater than any index in a particular year;
    # i.e. for a year y, end_by_year[y] = max(papers(y)) + 1.
    end_by_year = df.groupby('year')['paper_id'].count().sort_index().cumsum()
    # assert end_by_year[YEAR_SENTINEL] == len(df)
    # The sentinel is a very big number. Drop it for convenience.
    # end_by_year.drop(YEAR_SENTINEL, inplace=True)
    years_start = int(end_by_year.index.min())  # Smallest year
    years_end = int(end_by_year.index.max()) + 1  # Greatest year + 1.
    years_dict = {str(years_start): 0}  # First year starts at index 0.
    last = 0  # Filler in case years with no papers arise.
    for year in range(years_start, years_end):
        # JSON needs the key to be a string.
        # The end of year y is the start of year y + 1.
        years_dict[str(year + 1)] = last = int(end_by_year.get(year, last))
    with open(path, 'w') as f:
        json.dump(years_dict, f)


def process_paper_listings(
    in_path,
    out_path_id2ind, out_path_ind2id,
    out_path_year_bounds,
):
    """Load and process the table listing papers.

    The table is at in_path. A map of ID to index is written to
    out_path_id2ind, and a map of index to ID is written to
    out_path_ind2id. The paper index range per year is written to
    out_path_year_bounds.

    Returns:
    1. a map of paper ID to index,
    2. a DataFrame of paper ID and corresponding journal ID,
    3. a DataFrame of paper ID and corresponding conference series ID,
    4. the total number of papers.
    """
    with open(out_path_ind2id, 'wb') as ind_to_id_f:
        df, paper_journals_df = load_papers_df(in_path)
        papers_count = len(df)
        id_arr = df['paper_id'].to_numpy()
        ind_to_id_f.write(id_arr)  # Index to ID: copy the array of IDS.

    hashutil.make_id_hash_map(id_arr, out_path_id2ind)
    save_paper_years(df, out_path_year_bounds)
    del df  # Free memory.

    ind2id_map = hashutil.Ind2IdMap(out_path_ind2id)
    id2ind_map = hashutil.Id2IndHashMap(out_path_id2ind, ind2id_map)
    return id2ind_map, paper_journals_df, papers_count


def save_entity_counts(counts, path):
    """Save entity counts to 'path' as a JSON file."""
    authors_n, aff_n, fos_n, journals_n = counts
    with open(path, 'w') as f:
        json.dump({'authors': authors_n, 'aff': aff_n, 'fos': fos_n,
                   'journals': journals_n}, f)


def make_dataset(in_path, out_path):
    """Run the script, reading from in_path and writing to out_path."""
    in_path = pathlib.Path(in_path)
    out_path = pathlib.Path(out_path)

    logger.info('(0/7) making entity id to index map')
    # Looks convoluted, but see `process_entity_listings` docstring.
    entities_id2ind_maps, entities_counts = process_entity_listings(
        in_path, out_path, 'entities-ind2id.bin',
        [('authors', 'author', None, None, None),
         ('institutions', 'affltn', None, None, None),
         ('concepts', 'fos', None, None, None),
         ('sources', 'journl', None, None, None)])
    save_entity_counts(entities_counts, out_path / 'entity-counts.json')
    authors_id2ind, aff_id2ind, fos_id2ind, journals_id2ind \
        = entities_id2ind_maps

    logger.info('(1/7) making paper id to index map')
    papers_id2ind, paper_journals_df, papers_count \
        = process_paper_listings(in_path / 'works.txt',
                                 out_path / 'paper-id2ind.bin',
                                 out_path / 'paper-ind2id.bin',
                                 out_path / 'paper-years.json')

    logger.info('(2/7) loading MAG graph')
    citations_df = load_citations_df(in_path / 'PaperReferences.txt')
    authorships_df, paper_aff_df \
        = load_authorships_df(in_path / 'PaperAuthorAffiliations.txt')
    paper_fos_df = load_paper_fos_df(in_path / 'PaperFieldsOfStudy.txt')

    logger.info('(3/7) converting MAG IDs to internal indices')
    with authors_id2ind, aff_id2ind, fos_id2ind, journals_id2ind:
        # The context manager will close the mmaps for us.
        authors_id2ind.convert_inplace(authorships_df['author_id'])
        aff_id2ind.convert_inplace(paper_aff_df['affiliation_id'])
        journals_id2ind.convert_inplace(paper_journals_df['journal_id'])

        fos_id2ind.convert_inplace(paper_fos_df['fos_id'], allow_missing=True)
        paper_fos_df = paper_fos_df[paper_fos_df['fos_id'] != INDEX_SENTINEL]
        paper_fos_df.reset_index(drop=True, inplace=True)

    with papers_id2ind:
        papers_id2ind.convert_inplace(authorships_df['paper_id'])
        papers_id2ind.convert_inplace(paper_aff_df['paper_id'])
        papers_id2ind.convert_inplace(paper_journals_df['paper_id'])
        papers_id2ind.convert_inplace(paper_fos_df['paper_id'])

        papers_id2ind.convert_inplace(citations_df['citor_id'])
        papers_id2ind.convert_inplace(citations_df['citee_id'])

    logger.info('(4/7) writing edges: entities -> papers')
    # See `make_sparse_matrix` docstring.
    sparseutil.make_sparse_matrix(
        sum(entities_counts),
        [[(authorships_df['author_id'], authorships_df['paper_id']),
          (paper_aff_df['affiliation_id'], paper_aff_df['paper_id']),
          (paper_journals_df['journal_id'], paper_journals_df['paper_id']),
          (paper_fos_df['fos_id'], paper_fos_df['paper_id'])]],
        out_path / 'entity2paper-ptr.bin', out_path / 'entity2paper-ind.bin')

    logger.info('(5/7) writing edges: papers -> entities')
    sparseutil.make_sparse_matrix(
        papers_count,
        [[(authorships_df['paper_id'], authorships_df['author_id']),
          (paper_aff_df['paper_id'], paper_aff_df['affiliation_id']),
          (paper_journals_df['paper_id'], paper_journals_df['journal_id']),
          (paper_fos_df['paper_id'], paper_fos_df['fos_id'])]],
        out_path / 'paper2entity-ptr.bin',
        out_path / 'paper2entity-ind.bin')

    logger.info('(6/7) writing edges: papers -> citors, citees')
    sparseutil.make_sparse_matrix(
        papers_count,
        [[(citations_df['citee_id'], citations_df['citor_id'])],
         [(citations_df['citor_id'], citations_df['citee_id'])]],
        out_path / 'paper2citor-citee-ptr.bin',
        out_path / 'paper2citor-citee-ind.bin')

    logger.info('(7/7) done')


def main():
    """Run the script, saving the data to 'bingraph'."""
    stream_handler = logging.StreamHandler()  # Log to stderr.
    try:
        logger.addHandler(stream_handler)
        make_dataset('/data_seoul/openalex/openalex-snapshot/data/',
                     'bingraph-openalex')
    finally:
        logger.removeHandler(stream_handler)


if __name__ == '__main__':
    main()
