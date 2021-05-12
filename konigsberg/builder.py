import csv
import json
import pathlib
import pickle

import numpy as np
import pandas as pd

import hashutil
import sparseutil


class MAGDialect(csv.Dialect):
    delimiter = '\t'
    doublequote = False
    escapechar = None
    lineterminator = '\r\n'
    quotechar = None
    quoting = csv.QUOTE_NONE
    skipinitialspace = False
    strict = True


def load_authors_df(f):
    authors_df = pd.read_csv(
        f,
        dialect=MAGDialect(),
        engine='c',
        usecols=[0,1],
        names=['author_id', 'rank'],
        dtype={'author_id': np.uint32, 'rank': np.uint16},
        na_filter=False)
    authors_df.sort_values(
        'rank', inplace=True, ignore_index=True, kind='mergesort')
    del authors_df['rank']
    return authors_df


def load_fields_of_study_df(f):
    fields_of_study_df = pd.read_csv(
        f,
        dialect=MAGDialect(),
        engine='c',
        usecols=[0,1],
        names=['field_of_study_id', 'rank'],
        dtype={'field_of_study_id': np.uint32, 'rank': np.uint16},
        na_filter=False)
    fields_of_study_df.sort_values(
        'rank', inplace=True, ignore_index=True, kind='mergesort')
    del fields_of_study_df['rank']
    return fields_of_study_df


def load_papers_df(f):
    papers_df = pd.read_csv(
        f,
        dialect=MAGDialect(),
        engine='c',
        usecols=[0,1,7],
        names=['paper_id', 'rank', 'year'],
        dtype={'paper_id': np.uint32,
               'rank': np.uint16,
               'year': pd.UInt16Dtype()},
        keep_default_na=False,
        na_values={'year': ['']})
    papers_df.sort_values(
        'rank', inplace=True, ignore_index=True, kind='mergesort')
    papers_df.sort_values(
        'year', inplace=True, ignore_index=True, kind='mergesort')
    del papers_df['rank']
    papers_df['year'].fillna(np.uint16(-1), inplace=True)
    papers_df['year'] = papers_df['year'].astype(np.uint16)
    return papers_df


def load_citations_df(f):
    citations_df = pd.read_csv(
        f,
        dialect=MAGDialect(),
        engine='c',
        names=['citor_paper_id', 'citee_paper_id'],
        dtype=np.uint32,
        na_filter=False)
    return citations_df


def load_authorships_df(f):
    authorships_df = pd.read_csv(
        f,
        dialect=MAGDialect(),
        engine='c',
        usecols=[0,1],
        names=['paper_id', 'author_id'],
        dtype=np.uint32,
        na_filter=False)
    authorships_df.drop_duplicates(inplace=True, ignore_index=True)
    return authorships_df


def load_journals(f):
    journals_df = pd.read_csv(
        f,
        dialect=MAGDialect(),
        engine='c',
        usecols=[0,1],
        names=['journal_id', 'rank'],
        dtype={'journal_id': np.uint32, 'rank': np.uint16},
        na_filter=False)
    journals_df.sort_values(
        'rank', inplace=True, ignore_index=True, kind='mergesort')
    del journals_df['rank']
    return journals_df


def load_conference_series(f):
    conference_series_df = pd.read_csv(
        f,
        dialect=MAGDialect(),
        engine='c',
        usecols=[0,1],
        names=['conference_series_id', 'rank'],
        dtype={'conference_series_id': np.uint32, 'rank': np.uint16},
        na_filter=False)
    conference_series_df.sort_values(
        'rank', inplace=True, ignore_index=True, kind='mergesort')
    del conference_series_df['rank']
    return conference_series_df


def load_paper_fields_studied_df(f):
    paper_fields_studied_df = pd.read_csv(
        f,
        dialect=MAGDialect(),
        engine='c',
        usecols=[0,1],
        names=['paper_id', 'field_of_study_id'],
        dtype=np.uint32,
        na_filter=False)
    return paper_fields_studied_df


def load_paper_journals_df(f):
    paper_journals_df = pd.read_csv(
        f,
        dialect=MAGDialect(),
        engine='c',
        usecols=[0,10],
        names=['paper_id', 'journal_id'],
        dtype={'paper_id': np.uint32, 'journal_id': pd.UInt32Dtype()},
        keep_default_na=False,
        na_values={'journal_id': ['']})
    paper_journals_df.dropna(subset=['journal_id'], inplace=True)
    paper_journals_df['journal_id'] \
        = paper_journals_df['journal_id'].astype(np.uint32)
    return paper_journals_df


def load_paper_conference_series_df(f):
    paper_conference_series_df = pd.read_csv(
        f,
        dialect=MAGDialect(),
        engine='c',
        usecols=[0,11],
        names=['paper_id', 'conference_series_id'],
        dtype={'paper_id': np.uint32, 'conference_series_id': pd.UInt32Dtype()},
        keep_default_na=False,
        na_values={'conference_series_id': ['']})
    paper_conference_series_df.dropna(
        subset=['conference_series_id'], inplace=True)
    paper_conference_series_df['conference_series_id'] \
        = paper_conference_series_df['conference_series_id'].astype(np.uint32)
    return paper_conference_series_df


def make_mag_id_index_inplace(df, mag_colname, own_colname):
    df[own_colname] = df.index.to_numpy(np.uint32)
    df.index = df[mag_colname]
    del df[mag_colname]


def replace_ids_inplace(df, colname, mapping):
    df[colname] = df[colname].map(mapping)


def save_paper_years_inplace(df, path):
    start_by_year = df.groupby('year')['new_paper_id'].aggregate('min')
    del df['year']
    no_year_val = (1 << 16) - 1
    if no_year_val in start_by_year:
        no_year_start = start_by_year[no_year_val]
    else:
        no_year_start = len(df)
    del start_by_year[no_year_val]
    min_year = int(start_by_year.index.min())
    max_year = int(start_by_year.index.max()) + 1
    start_by_year[max_year] = no_year_start
    for year in range(max_year - 1, min_year, -1):
        if year not in start_by_year:
            start_by_year[year] = start_by_year[year + 1]  # Length 0
    years_dict = {
        str(year): int(min_id) for year, min_id in start_by_year.iteritems()}
    with open(path / 'paper-years.json', 'w') as f:
        json.dump(years_dict, f)


def save_citations(df, n_papers, path):
    sparseutil.make_sparse_matrix(
        df['citor_paper_id'], df['citee_paper_id'], n_papers,
        path / 'citor2citee-indptr.bin', path / 'citor2citee-indices.bin')
    sparseutil.make_sparse_matrix(
        df['citee_paper_id'], df['citor_paper_id'], n_papers,
        path / 'citee2citor-indptr.bin', path / 'citee2citor-indices.bin')


def save_paper_fields_studied(df, n_papers, n_fields_of_study, path):
    sparseutil.make_sparse_matrix(
        df['paper_id'], df['field_of_study_id'], n_papers, path / 'paper2fos')
    sparseutil.make_sparse_matrix(
        df['field_of_study_id'], df['paper_id'], n_fields_of_study,
        path / 'fos2paper')


def save_authorships(df, n_papers, n_authors, path):
    sparseutil.make_sparse_matrix(
        df['paper_id'], df['author_id'], n_papers,
        path / 'paper2author-indptr.bin', path / 'paper2author-indices.bin')
    sparseutil.make_sparse_matrix(
        df['author_id'], df['paper_id'], n_authors,
        path / 'author2paper-indptr.bin', path / 'author2paper-indices.bin')


def get_dataset(in_path, out_path):
    in_path = pathlib.Path(in_path)
    out_path = pathlib.Path(out_path)

    authors_path = in_path / 'Authors.txt'
    papers_path = in_path / 'Papers.txt'
    citations_path = in_path / 'PaperReferences.txt'
    authorships_path = in_path / 'PaperAuthorAffiliations.txt'
    fields_of_study_path = in_path / 'FieldsOfStudy.txt'
    paper_fields_studied_path = in_path / 'PaperFieldsOfStudy.txt'
    journals_path = in_path / 'Journals.txt'
    conference_series_path = in_path / 'ConferenceSeries.txt'

    # papers_df = load_papers_df(papers_path)
    # make_mag_id_index_inplace(papers_df, 'paper_id', 'new_paper_id')
    # with open(out_path / 'papers-index.pkl', 'wb') as f:
    # #     pickle.dump(papers_df, f)
    # print('unpickling papers')
    # with open(out_path / 'papers-index.pkl', 'rb') as f:
    #     papers_df = pickle.load(f)
    # save_paper_years_inplace(papers_df, out_path)
    # n_papers = len(papers_df)

    # print('loading citations')
    # citations_df = load_citations_df(citations_path)
    # print('replacing1')
    # replace_ids_inplace(citations_df, 'citor_paper_id',
    #                     papers_df['new_paper_id'])
    # print('replacing2')
    # replace_ids_inplace(citations_df, 'citee_paper_id',
    #                     papers_df['new_paper_id'])
    # print('pickling citations')
    # try:
    #     with open(out_path / 'citations-table.pkl', 'wb') as f:
    #         pickle.dump(citations_df, f, pickle.HIGHEST_PROTOCOL)
    # except Exception:
    #     breakpoint()/
    # print('unpickling citations')
    # with open(out_path / 'citations-table.pkl', 'rb') as f:
    #     citations_df = pickle.load(f)
    # print('saving citations')
    # save_citations(citations_df, n_papers, out_path)
    # del citations_df  # Free memory

    # print('loading authorships')
    # authorships_df = load_authorships_df(authorships_path)
    
    # print('unpickling papers')
    # with open(out_path / 'papers-index.pkl', 'rb') as f:
    #     papers_df = pickle.load(f)
    # n_papers = len(papers_df)
    # print('replacing1')
    # replace_ids_inplace(authorships_df, 'paper_id', papers_df['new_paper_id'])
    # del papers_df  # Free memory

    # authors_df = load_authors_df(authors_path)
    # make_mag_id_index_inplace(authors_df, 'author_id', 'new_author_id')
    # with open(out_path / 'authors-index.pkl', 'wb') as f:
    #     pickle.dump(authors_df, f)

    # print('unpickling authorships')
    # with open(out_path / 'authorships-table.pkl', 'rb') as f:
    #     authorships_df = pickle.load(f)

    # print('unpickling authors')
    # with open(out_path / 'authors-index.pkl', 'rb') as f:
    #     authors_df = pickle.load(f)
    # hashutil.make_id_hash_map(authors_df.index.to_numpy().astype(np.uint32), out_path / 'author-id-map')
    # n_authors = len(authors_df)
    # print('replacing2')
    # replace_ids_inplace(authorships_df, 'author_id', authors_df['new_author_id'])
    # del authors_df  # Free memory
    # print('pickling authorships')
    # try:
    #     with open(out_path / 'authorships-table.pkl', 'wb') as f:
    #         pickle.dump(authorships_df, f, pickle.HIGHEST_PROTOCOL)
    # except Exception:
    #     breakpoint()
    # print('saving authorships')
    # save_authorships(authorships_df, n_papers, n_authors, out_path)
    # del authorships_df

    # print('loading fields of study')
    # fields_of_study_df = load_fields_of_study_df(fields_of_study_path)
    # print('replacing ids')
    # make_mag_id_index_inplace(fields_of_study_df,
    #                           'field_of_study_id', 'new_field_of_study_id')
    # print('pickling fields of study')
    # with open(out_path / 'fields-of-study-table.pkl', 'wb') as f:
    #     pickle.dump(fields_of_study_df, f, pickle.HIGHEST_PROTOCOL)

    # print('unpickling fields of study')
    # with open(out_path / 'fields-of-study-table.pkl', 'rb') as f:
    #     fields_of_study_df = pickle.load(f)
    # n_fields_of_study = len(fields_of_study_df)
    # print('loading paper fields studied')
    # paper_fields_studied_df = load_paper_fields_studied_df(
    #     paper_fields_studied_path)
    # print('replacing fos ids')
    # replace_ids_inplace(paper_fields_studied_df, 'field_of_study_id',
    #                     fields_of_study_df['new_field_of_study_id'])
    # del fields_of_study_df
    # print('unpickling papers')
    # with open(out_path / 'papers-index.pkl', 'rb') as f:
    #     papers_df = pickle.load(f)
    # n_papers = len(papers_df)
    # print('replacing paper ids')
    # replace_ids_inplace(paper_fields_studied_df, 'paper_id',
    #                     papers_df['new_paper_id'])
    # print('pickling paper fields of studied')
    # with open(out_path / 'paper-fields-studied-table.pkl', 'wb') as f:
    #     pickle.dump(paper_fields_studied_df, f, pickle.HIGHEST_PROTOCOL)

    # print('unpickling fields of study')
    # with open(out_path / 'fields-of-study-table.pkl', 'rb') as f:
    #     fields_of_study_df = pickle.load(f)
    # n_fields_of_study = len(fields_of_study_df)
    # del fields_of_study_df

    # print('unpickling papers')
    # with open(out_path / 'papers-index.pkl', 'rb') as f:
    #     papers_df = pickle.load(f)
    # n_papers = len(papers_df)
    # del papers_df

    # # hashutil.make_id_hash_map(
    # #     fields_of_study_df.index.to_numpy().astype(np.uint32),
    # #     out_path / 'field-of-study-id-map')


    # print('unpickling paper fields studied')
    # with open(out_path / 'paper-fields-studied-table.pkl', 'rb') as f:
    #     paper_fields_studied_df = pickle.load(f)
    # print('saving paper fields studied')
    # save_paper_fields_studied(
    #     paper_fields_studied_df, n_papers, n_fields_of_study, out_path)

    # journals_df = load_journals(journals_path)
    # make_mag_id_index_inplace(journals_df, 'journal_id', 'new_journal_id')
    # print('making journal map')
    # hashutil.make_id_hash_map(journals_df.index.to_numpy().astype(np.uint32),
    #                           out_path / 'journal-id-map')
    # n_journals = len(journals_df)

    # print('loading paper journals')
    # paper_journals_df = load_paper_journals_df(papers_path)

    # print('replacing journal ids')
    # replace_ids_inplace(paper_journals_df, 'journal_id',
    #                     journals_df['new_journal_id'])
    # del journals_df

    # print('unpickling papers')
    # with open(out_path / 'papers-index.pkl', 'rb') as f:
    #     papers_df = pickle.load(f)
    # n_papers = len(papers_df)

    # print('replacing paper ids')
    # replace_ids_inplace(paper_journals_df, 'paper_id',
    #                     papers_df['new_paper_id'])
    # del papers_df

    # print('pickling paper journals')
    # with open(out_path / 'paper-journals-table.pkl', 'wb') as f:
    #     pickle.dump(paper_journals_df, f, pickle.HIGHEST_PROTOCOL)
    # # print('unpickling paper journals')
    # # with open(out_path / 'paper-journals-table.pkl', 'rb') as f:
    # #     paper_journals_df = pickle.load(f)

    # print('making journal to paper graph')
    # sparseutil.make_sparse_matrix(
    #     paper_journals_df['journal_id'], paper_journals_df['paper_id'],
    #     n_journals, out_path / 'journal2paper')

    # print('making paper to journal')
    # sparseutil.make_sparse_vector(
    #     paper_journals_df['paper_id'],
    #     paper_journals_df['journal_id'],
    #     n_papers, out_path / 'paper2journal.bin')

    # conference_series_df = load_conference_series(conference_series_path)
    # make_mag_id_index_inplace(conference_series_df, 'conference_series_id', 'new_conference_series_id')
    # print('making conference series map')
    # hashutil.make_id_hash_map(conference_series_df.index.to_numpy().astype(np.uint32),
    #                           out_path / 'conference-series-id-map')
    # n_conference_series = len(conference_series_df)

    # print('loading paper conference series')
    # paper_conference_series_df = load_paper_conference_series_df(papers_path)

    # print('replacing conference series ids')
    # replace_ids_inplace(paper_conference_series_df, 'conference_series_id',
    #                     conference_series_df['new_conference_series_id'])
    # del conference_series_df

    # print('unpickling papers')
    # with open(out_path / 'papers-index.pkl', 'rb') as f:
    #     papers_df = pickle.load(f)
    # n_papers = len(papers_df)

    # print('replacing paper ids')
    # replace_ids_inplace(paper_conference_series_df, 'paper_id',
    #                     papers_df['new_paper_id'])
    # del papers_df

    # print('pickling paper conference series')
    # with open(out_path / 'paper-conference-series-table.pkl', 'wb') as f:
    #     pickle.dump(paper_conference_series_df, f, pickle.HIGHEST_PROTOCOL)
    # # print('unpickling paper conference series')
    # # with open(out_path / 'paper-conference-series-table.pkl', 'rb') as f:
    # #     paper_conference_series_df = pickle.load(f)

    # print('making conference series to paper graph')
    # sparseutil.make_sparse_matrix(
    #     paper_conference_series_df['conference_series_id'], paper_conference_series_df['paper_id'],
    #     n_conference_series, out_path / 'cs2paper')

    # print('making paper to conference series')
    # sparseutil.make_sparse_vector(
    #     paper_conference_series_df['paper_id'],
    #     paper_conference_series_df['conference_series_id'],
    #     n_papers, out_path / 'paper2cs.bin')





def main():
    get_dataset('/data/u1033719/graph/mag-2019-11-08/', 'bingraph')
