import csv
import json
import logging
import pathlib

import numpy as np
import pandas as pd

import hashutil
import sparseutil

YEAR_SENTINEL = np.uint16(-1)  # Denotes missing year
INDEX_SENTINEL = np.uint32(-1)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class MAGDialect(csv.Dialect):
    """Microsoft Academic Graph table file format."""
    delimiter = '\t'
    doublequote = False
    escapechar = None
    lineterminator = '\r\n'
    quotechar = None
    quoting = csv.QUOTE_NONE
    skipinitialspace = False
    strict = True


def load_entity_df(path, filter_column=None):
    indices = [0, 1]
    names = ['id', 'rank']
    dtypes = {'id': np.uint32, 'rank': np.uint16}
    if filter_column:
        filter_col_i, filter_col_name, filter_col_dtype, _ = filter_column
        indices.append(filter_col_i)
        names.append(filter_col_name)
        dtypes[filter_col_name] = filter_col_dtype
    df = pd.read_csv(
        path,
        dialect=MAGDialect(), engine='c', na_filter=False,
        usecols=indices, names=names, dtype=dtypes)
    if filter_column:
        _, filter_col_name, _, filter_f = filter_column
        df = df[filter_f(df[filter_col_name])]
        df.reset_index(drop=True, inplace=True)
        del df[filter_col_name]
    df.sort_values('rank', inplace=True, ignore_index=True, kind='mergesort')
    del df['rank']
    return df


def process_entity_listings(entity_paths, out_path_ind2id):
    counts = []
    with open(out_path_ind2id, 'wb') as ind_to_id_f:
        offset = 0
        for in_path, out_path_id2ind, filter_info in entity_paths:
            df = load_entity_df(in_path, filter_info)
            id_arr = df['id'].to_numpy()
            ind_to_id_f.write(id_arr)
            hashutil.make_id_hash_map(id_arr, out_path_id2ind, offset)
            count = len(df)
            counts.append(count)
            offset += count

    ind2id_map = hashutil.Ind2IdMap(out_path_ind2id)
    id2ind_maps = tuple(hashutil.Id2IndHashMap(path, ind2id_map)
                        for _, path, _ in entity_paths)
    return id2ind_maps, counts


def load_papers_df(path):
    df = pd.read_csv(
        path,
        dialect=MAGDialect(), engine='c',
        usecols=[0, 1, 7, 10, 11],
        names=['paper_id', 'rank', 'year', 'journal_id', 'cs_id'],
        dtype={'paper_id': np.uint32, 'rank': np.uint16,
               'year': pd.UInt16Dtype(), 'journal_id': pd.UInt32Dtype(),
               'cs_id': pd.UInt32Dtype()},
        keep_default_na=False,
        na_values={'year': [''], 'journal_id': [''], 'cs_id': ['']})

    paper_journals_df = df.loc[df['journal_id'].notna(),
                               ['paper_id', 'journal_id']]
    paper_journals_df.reset_index(drop=True, inplace=True)
    paper_journals_df['journal_id'] \
        = paper_journals_df['journal_id'].astype(np.uint32)
    del df['journal_id']
    paper_cs_df = df.loc[df['cs_id'].notna(), ['paper_id', 'cs_id']]
    paper_cs_df.reset_index(drop=True, inplace=True)
    paper_cs_df['cs_id'] = paper_cs_df['cs_id'].astype(np.uint32)
    del df['cs_id']

    df['year'].fillna(YEAR_SENTINEL, inplace=True)
    df['year'] = df['year'].astype(np.uint16)
    df.sort_values('rank', inplace=True, ignore_index=True, kind='mergesort')
    del df['rank']
    df.sort_values('year', inplace=True, ignore_index=True, kind='mergesort')

    return df, paper_journals_df, paper_cs_df


def load_authorships_df(path):
    df = pd.read_csv(
        path,
        dialect=MAGDialect(), engine='c',
        usecols=[0, 1, 2], names=['paper_id', 'author_id', 'affiliation_id'],
        dtype={'paper_id': np.uint32, 'author_id': np.uint32,
               'affiliation_id': pd.UInt32Dtype()},
        keep_default_na=False, na_values={'affiliation_id': ['']})

    paper_affiliations_df = df.loc[df['affiliation_id'].notna(),
                                   ['paper_id', 'affiliation_id']]
    paper_affiliations_df.reset_index(drop=True, inplace=True)
    paper_affiliations_df['affiliation_id'] \
        = paper_affiliations_df['affiliation_id'].astype(np.uint32)
    del df['affiliation_id']
    return df, paper_affiliations_df


def load_many_to_many_mapping(path, colname1, colname2):
    return pd.read_csv(
        path,
        dialect=MAGDialect(), engine='c', na_filter=False,
        usecols=[0, 1], names=[colname1, colname2],
        dtype={colname1: np.uint32, colname2: np.uint32})


def load_citations_df(path):
    return load_many_to_many_mapping(path, 'citor_id', 'citee_id')


def load_paper_fos_df(path):
    return load_many_to_many_mapping(path, 'paper_id', 'fos_id')


def save_paper_years(df, path):
    end_by_year = df.groupby('year')['paper_id'].count().sort_index().cumsum()
    assert end_by_year[YEAR_SENTINEL] == len(df)
    end_by_year.drop(YEAR_SENTINEL, inplace=True)
    years_start = int(end_by_year.index.min())
    years_end = int(end_by_year.index.max()) + 1
    years_dict = {str(years_start): 0}
    last = 0
    for year in range(years_start, years_end):
        years_dict[str(year + 1)] = last = int(end_by_year.get(year, last)) 
    with open(path, 'w') as f:
        json.dump(years_dict, f)


def process_paper_listings(
    in_path,
    out_path_id2ind, out_path_ind2id,
    out_path_year_bounds,
):
    with open(out_path_ind2id, 'wb') as ind_to_id_f:
        df, paper_journals_df, paper_cs_df = load_papers_df(in_path)
        papers_count = len(df)
        id_arr = df['paper_id'].to_numpy()
        ind_to_id_f.write(id_arr)
    
    hashutil.make_id_hash_map(id_arr, out_path_id2ind)
    save_paper_years(df, out_path_year_bounds)
    del df

    ind2id_map = hashutil.Ind2IdMap(out_path_ind2id)
    id2ind_map = hashutil.Id2IndHashMap(out_path_id2ind, ind2id_map)
    return id2ind_map, paper_journals_df, paper_cs_df, papers_count


def save_entity_counts(counts, path):
    authors_n, aff_n, fos_n, journals_n, cs_n = counts
    with open(path, 'w') as f:
        json.dump({'authors': authors_n, 'aff': aff_n, 'fos': fos_n,
                   'journals': journals_n, 'cs': cs_n}, f)


def make_dataset(in_path, out_path):
    in_path = pathlib.Path(in_path)
    out_path = pathlib.Path(out_path)

    logger.info('(0/7) making entity id to index map')
    entities_id2ind_maps, entities_counts = process_entity_listings(
        [(in_path / 'Authors.txt', out_path / 'author-id2ind.bin', None),
         (in_path / 'Affiliations.txt', out_path / 'affltn-id2ind.bin', None),
         (in_path / 'FieldsOfStudy.txt', out_path / 'fos-id2ind.bin',
          (5, 'level', np.uint8, lambda level: level <= 1)),
         (in_path / 'Journals.txt', out_path / 'journl-id2ind.bin', None),
         (in_path / 'ConferenceSeries.txt', out_path / 'cs-id2ind.bin', None)],
        out_path / 'entities-ind2id.bin')
    save_entity_counts(entities_counts, out_path / 'entity-counts.json')
    authors_id2ind, aff_id2ind, fos_id2ind, journals_id2ind, cs_id2ind \
        = entities_id2ind_maps

    logger.info('(1/7) making paper id to index map')
    papers_id2ind, paper_journals_df, paper_cs_df, papers_count \
        = process_paper_listings(in_path / 'Papers.txt',
                                 out_path / 'paper-id2ind.bin',
                                 out_path / 'paper-ind2id.bin',
                                 out_path / 'paper-years.json')

    logger.info('(2/7) loading MAG graph')
    citations_df = load_citations_df(in_path / 'PaperReferences.txt')
    authorships_df, paper_aff_df \
        = load_authorships_df(in_path / 'PaperAuthorAffiliations.txt')
    paper_fos_df = load_paper_fos_df(in_path / 'PaperFieldsOfStudy.txt')

    logger.info('(3/7) converting MAG IDs to indices')
    with authors_id2ind, aff_id2ind, fos_id2ind, journals_id2ind, cs_id2ind:
        authors_id2ind.convert_inplace(authorships_df['author_id'])
        aff_id2ind.convert_inplace(paper_aff_df['affiliation_id'])
        journals_id2ind.convert_inplace(paper_journals_df['journal_id'])
        cs_id2ind.convert_inplace(paper_cs_df['cs_id'])

        fos_id2ind.convert_inplace(paper_fos_df['fos_id'], allow_missing=True)
        paper_fos_df = paper_fos_df[paper_fos_df['fos_id'] != INDEX_SENTINEL]
        paper_fos_df.reset_index(drop=True, inplace=True)

    with papers_id2ind:
        papers_id2ind.convert_inplace(authorships_df['paper_id'])
        papers_id2ind.convert_inplace(paper_aff_df['paper_id'])
        papers_id2ind.convert_inplace(paper_journals_df['paper_id'])
        papers_id2ind.convert_inplace(paper_cs_df['paper_id'])
        papers_id2ind.convert_inplace(paper_fos_df['paper_id'])

        papers_id2ind.convert_inplace(citations_df['citor_id'])
        papers_id2ind.convert_inplace(citations_df['citee_id'])

    logger.info('(4/7) writing edges: entities -> papers')
    sparseutil.make_sparse_matrix(
        sum(entities_counts),
        [[(authorships_df['author_id'], authorships_df['paper_id']),
          (paper_aff_df['affiliation_id'], paper_aff_df['paper_id']),
          (paper_journals_df['journal_id'], paper_journals_df['paper_id']),
          (paper_cs_df['cs_id'], paper_cs_df['paper_id']),
          (paper_fos_df['fos_id'], paper_fos_df['paper_id'])]],
        out_path / 'entity2paper-ptr.bin', out_path / 'entity2paper-ind.bin')

    logger.info('(5/7) writing edges: papers -> entities')
    sparseutil.make_sparse_matrix(
        papers_count,
        [[(authorships_df['paper_id'], authorships_df['author_id']),
          (paper_aff_df['paper_id'], paper_aff_df['affiliation_id']),
          (paper_journals_df['paper_id'], paper_journals_df['journal_id']),
          (paper_cs_df['paper_id'], paper_cs_df['cs_id']),
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
    stream_handler = logging.StreamHandler()  # Log to stderr.
    try:
        logger.addHandler(stream_handler)
        make_dataset('/data/u1033719/graph/mag-2019-11-08/', 'bingraph')
    finally:
        logger.removeHandler(stream_handler)


if __name__ == '__main__':
    main()
