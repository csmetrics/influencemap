import csv
import json
import logging
import pathlib
import re
import time

import numpy as np
import pandas as pd

import hashutil
import sparseutil

YEAR_SENTINEL = np.uint16(-1)  # Denotes missing year
INDEX_SENTINEL = np.uint64(-1)  # Denotes deleted entity

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
    """
    indices = [0, 1]
    names = ['id', 'works_count']
    dtypes = {'id': str, 'works_count': np.uint16}
    if filter_column:
        filter_col_i, filter_col_name, filter_col_dtype, _ = filter_column
        indices.append(filter_col_i)
        names.append(filter_col_name)
        dtypes[filter_col_name] = filter_col_dtype

    part_files = path.glob('updated_date=*/part_*')
    df_list = []
    for file in part_files:
        data = []
        for line in open(file, 'r'):
            try:
                json_data = json.loads(line)
                data.append(json_data)
            except json.JSONDecodeError:
                print(f"Error parsing JSON: {line}")
        df_part = pd.DataFrame(data)[names]
        df_part['id'] = df_part['id'].str.extract(r'[A-Z](\d+)$').astype(np.uint64)
        # print(df_part)
        df_list.append(df_part)
    df = pd.concat(df_list, ignore_index=True)

    meta = None if meta_func is None else meta_func(df)
    if sort_column:
        df.sort_values(
            sort_column, inplace=True, ignore_index=True, kind='mergesort')
    if filter_column:
        _, filter_col_name, _, filter_f = filter_column
        df = df[filter_f(df[filter_col_name])]
        df.reset_index(drop=True, inplace=True)  # Save memory.
        del df[filter_col_name]
    df.sort_values('works_count', inplace=True, ignore_index=True, kind='mergesort')
    del df['works_count']
    return df, meta


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
                in_dir / in_fname,
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

    names=['paper_id', 'rank', 'year', 'journal_id']
    # dtype={'id': np.uint64, 'cited_by_count': np.uint16,
    #         'publication_year': pd.UInt16Dtype(), 'journal_id': pd.UInt64Dtype()}

    part_files = path.glob('updated_date=*/part_*')
    df_list = []
    for file in part_files:
        data = []
        for line in open(file, 'r'):
            try:
                json_data = json.loads(line)
                filtered_data = {
                    'paper_id': json_data['id'],
                    'rank': json_data['cited_by_count'],
                    'year': json_data['publication_year']
                }
                try:
                    source_str = json_data['primary_location']['source']['id']
                    source_id = int(re.search(r"\d+", source_str).group())
                except:
                    source_id = np.nan
                filtered_data['journal_id'] = source_id
                # print(filtered_data)
                data.append(filtered_data)
            except json.JSONDecodeError:
                print(f"Error parsing JSON: {line}")
        try:
            df_part = pd.DataFrame(data)[names]
            df_part['paper_id'] = df_part['paper_id'].str.extract(r'[A-Z](\d+)$').astype(np.uint64)
            # print(df_part)
            df_list.append(df_part)
        except:
            pass
    df = pd.concat(df_list, ignore_index=True)

    # Make separate tables for paper-journal/conference series mappings.
    paper_journals_df = df.loc[df['journal_id'].notna(),
                               ['paper_id', 'journal_id']]
    paper_journals_df.reset_index(drop=True, inplace=True)  # Memory.
    paper_journals_df['journal_id'] = paper_journals_df['journal_id'].astype(np.uint64)
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
    part_files = path.glob('updated_date=*/part_*')
    df_list = []
    for i, file in enumerate(part_files):
        print("load_authorships_df {} {}".format(i, file))
        for line in open(file, 'r'):
            try:
                json_data = json.loads(line)
                filtered_data = {
                    'paper_id': json_data['id'],
                }
                try:
                    authors = [a['author']['id'] for a in json_data['authorships']]
                except:
                    authors = []
                if len(authors) == 0:
                    continue

                institutions = []
                for a in json_data['authorships']:
                    inst = None
                    try:
                        inst = re.search(r"\d+", a['institutions'][0]['id']).group()
                    except:
                        pass
                    institutions.append(inst)

                filtered_data['authors'] = authors
                filtered_data['institutions'] = institutions

                df_id = pd.DataFrame({'paper_id': [filtered_data['paper_id']]})
                df_referenced = pd.DataFrame({
                    'author_id': filtered_data['authors'],
                    'affiliation_id': filtered_data['institutions']
                })
                df_part = pd.merge(df_id, df_referenced, how='cross')

                df_part['paper_id'] = df_part['paper_id'].str.extract(r'[A-Z](\d+)$').astype(np.uint64)
                df_part['author_id'] = df_part['author_id'].str.extract(r'[A-Z](\d+)$').astype(np.uint64)
                # print(df_part)
            except Exception as e:
                print(f"Error parsing JSON: {line}")
        df_list.append(df_part)
    df = pd.concat(df_list, ignore_index=True)
    # print(df)

    paper_affiliations_df = df.loc[df['affiliation_id'].notna(),
                                   ['paper_id', 'affiliation_id']]
    paper_affiliations_df.reset_index(drop=True, inplace=True)
    paper_affiliations_df['affiliation_id'] = paper_affiliations_df['affiliation_id'].astype(np.uint64)
    del df['affiliation_id']
    return df, paper_affiliations_df


def load_citations_df(path):
    """Load table of citations."""
    part_files = path.glob('updated_date=*/part_*')
    df_list = []
    for i, file in enumerate(part_files):
        print("load_citations_df {} {}".format(i, file))
        for line in open(file, 'r'):
            try:
                json_data = json.loads(line)
                if len(json_data['referenced_works']) == 0:
                    continue
                df_id = pd.DataFrame({'citor_id': [json_data['id']]})
                df_referenced = pd.DataFrame({'citee_id': json_data['referenced_works']})
                df_part = pd.merge(df_id, df_referenced, how='cross')

                df_part['citor_id'] = df_part['citor_id'].str.extract(r'[A-Z](\d+)$').astype(np.uint64)
                df_part['citee_id'] = df_part['citee_id'].str.extract(r'[A-Z](\d+)$').astype(np.uint64)
                # print(df_part)
            except json.JSONDecodeError:
                print(f"Error parsing JSON: {line}")
        df_list.append(df_part)
    df = pd.concat(df_list, ignore_index=True)
    # print(df)
    return df


def load_paper_fos_df(path):
    """Load table of paper fields of study."""
    part_files = path.glob('updated_date=*/part_*')
    df_list = []
    for i, file in enumerate(part_files):
        print("load_paper_fos_df {} {}".format(i, file))
        for line in open(file, 'r'):
            try:
                json_data = json.loads(line)
                concepts = []
                for c in json_data['concepts']:
                    if c['level'] <= 1:
                        concepts.append(c['id'])
                if len(concepts) == 0:
                    continue
                df_id = pd.DataFrame({'paper_id': [json_data['id']]})
                df_referenced = pd.DataFrame({'fos_id': concepts})
                df_part = pd.merge(df_id, df_referenced, how='cross')

                df_part['paper_id'] = df_part['paper_id'].str.extract(r'[A-Z](\d+)$').astype(np.uint64)
                df_part['fos_id'] = df_part['fos_id'].str.extract(r'[A-Z](\d+)$').astype(np.uint64)
                # print(df_part)
            except json.JSONDecodeError:
                print(f"Error parsing JSON: {line}")
        df_list.append(df_part)
    df = pd.concat(df_list, ignore_index=True)
    # print(df)
    return df


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
    print("end_by_year", end_by_year)
    assert end_by_year[YEAR_SENTINEL] == len(df)
    # The sentinel is a very big number. Drop it for convenience.
    end_by_year.drop(YEAR_SENTINEL, inplace=True)
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

    time0 = time.time()
    logger.info('(0/7) making entity id to index map')
    # Looks convoluted, but see `process_entity_listings` docstring.
    entities_id2ind_maps, entities_counts = process_entity_listings(
        in_path, out_path, 'entities-ind2id.bin',
        [('authors', 'author', None, None, None),
         ('institutions', 'affltn', None, None, None),
         ('concepts', 'fos',
          lambda df: dict(level0count=int((df['level'] == 0).sum())),
          (5, 'level', np.uint8, lambda level: level <= 1), 'level'),
         ('sources', 'journl', None, None, None)])
    save_entity_counts(entities_counts, out_path / 'entity-counts.json')
    authors_id2ind, aff_id2ind, fos_id2ind, journals_id2ind \
        = entities_id2ind_maps
    time1 = time.time()
    logger.info('Done {}'.format(time1-time0))

    logger.info('(1/7) making paper id to index map')
    papers_id2ind, paper_journals_df, papers_count \
        = process_paper_listings(in_path / 'works',
                                 out_path / 'paper-id2ind.bin',
                                 out_path / 'paper-ind2id.bin',
                                 out_path / 'paper-years.json')
    time2 = time.time()
    logger.info('Done {}'.format(time2-time1))

    logger.info('(2/7) loading MAG graph')
    citations_df = load_citations_df(in_path / 'works')
    time3_1 = time.time()
    print("Done generating citations_df", time3_1-time2)
    authorships_df, paper_aff_df = load_authorships_df(in_path / 'works')
    time3_2 = time.time()
    print("Done generating authorships_df and paper_aff_df", time3_2-time3_1)
    paper_fos_df = load_paper_fos_df(in_path / 'works')
    time3_3 = time.time()
    print("Done generating load_paper_fos_df", time3_3-time3_2)

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
    time4 = time.time()
    logger.info('Done {}'.format(time4-time3_3))

    logger.info('(4/7) writing edges: entities -> papers')
    # See `make_sparse_matrix` docstring.
    sparseutil.make_sparse_matrix(
        sum(entities_counts),
        [[(authorships_df['author_id'], authorships_df['paper_id']),
          (paper_aff_df['affiliation_id'], paper_aff_df['paper_id']),
          (paper_journals_df['journal_id'], paper_journals_df['paper_id']),
          (paper_fos_df['fos_id'], paper_fos_df['paper_id'])]],
        out_path / 'entity2paper-ptr.bin', out_path / 'entity2paper-ind.bin')
    time5 = time.time()
    logger.info('Done {}'.format(time5-time4))

    logger.info('(5/7) writing edges: papers -> entities')
    sparseutil.make_sparse_matrix(
        papers_count,
        [[(authorships_df['paper_id'], authorships_df['author_id']),
          (paper_aff_df['paper_id'], paper_aff_df['affiliation_id']),
          (paper_journals_df['paper_id'], paper_journals_df['journal_id']),
          (paper_fos_df['paper_id'], paper_fos_df['fos_id'])]],
        out_path / 'paper2entity-ptr.bin',
        out_path / 'paper2entity-ind.bin')
    time6 = time.time()
    logger.info('Done {}'.format(time6-time5))

    logger.info('(6/7) writing edges: papers -> citors, citees')
    sparseutil.make_sparse_matrix(
        papers_count,
        [[(citations_df['citee_id'], citations_df['citor_id'])],
         [(citations_df['citor_id'], citations_df['citee_id'])]],
        out_path / 'paper2citor-citee-ptr.bin',
        out_path / 'paper2citor-citee-ind.bin')
    time7 = time.time()
    logger.info('Done {}'.format(time7-time6))

    logger.info('(7/7) done')


def main():
    """Run the script, saving the data to 'bingraph'."""
    stream_handler = logging.StreamHandler()  # Log to stderr.
    try:
        logger.addHandler(stream_handler)
        make_dataset('/Users/minjeong.shin/Work/openalex/openalex-snapshot/data/', 'bingraph-openalex')
    finally:
        logger.removeHandler(stream_handler)


if __name__ == '__main__':
    main()
