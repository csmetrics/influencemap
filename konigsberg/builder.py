import csv
import pathlib
import pickle

import numpy as np
import pandas as pd

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


# def load_authors_df(f):
#     authors_df = pd.read_csv(
#         f,
#         dialect=MAGDialect(),
#         engine='c',
#         usecols=[0,1],
#         names=['author_id', 'rank'],
#         dtype={'author_id': np.uint32, 'rank': np.uint16},
#         na_filter=False,
#     )
#     authors_df.sort_values(
#         'rank',
#         inplace=True,
#         ignore_index=True,
#         kind='mergesort',
#     )
#     del authors_df['rank']
#     return authors_df


# def load_papers_df(f):
#     papers_df = pd.read_csv(
#         f,
#         dialect=MAGDialect(),
#         engine='c',
#         usecols=[0,1,7],
#         names=['paper_id', 'rank', 'year'],
#         dtype={'paper_id': np.uint32,
#                'rank': np.uint16,
#                'year': pd.UInt16Dtype()},
#         keep_default_na=False,
#         na_values={'year': ['']}
#     )
#     papers_df.sort_values(
#         'rank',
#         inplace=True,
#         ignore_index=True,
#         kind='mergesort',
#     )
#     papers_df.sort_values(
#         'year',
#         inplace=True,
#         ignore_index=True,
#         kind='mergesort',
#     )
#     del papers_df['rank']
#     papers_df['year'].fillna(np.uint16(-1), inplace=True)
#     papers_df['year'] = papers_df['year'].astype(np.uint16)
#     return papers_df


def load_citations_df(f):
    citations_df = pd.read_csv(
        f,
        dialect=MAGDialect(),
        engine='c',
        names=['citor_paper_id', 'citee_paper_id'],
        dtype=np.uint32,
        na_filter=False,
    )
    return citations_df


def load_authorships_df(f):
    authorships_df = pd.read_csv(
        f,
        dialect=MAGDialect(),
        engine='c',
        usecols=[0,1],
        names=['paper_id', 'author_id'],
        dtype=np.uint32,
        na_filter=False,
    )
    print('deduping authorships')
    authorships_df.drop_duplicates(inplace=True, ignore_index=True)
    return authorships_df


def make_mag_id_index_inplace(df, mag_colname, own_colname):
    df[own_colname] = df.index.to_numpy(np.uint32)
    df.index = df[mag_colname]
    del df[mag_colname]


def replace_ids_inplace(df, colname, mapping):
    df[colname] = df[colname].map(mapping)


def save_paper_years_inplace(df):
    # Save in /dev/null for now.
    del df['year']


def save_citations(df, n_papers, path):
    print('sc1')
    sparseutil.make_sparse_matrix(
        df['citor_paper_id'], df['citee_paper_id'], n_papers,
        path / 'citor2citee-indptr.bin', path / 'citor2citee-indices.bin')
    print('sc2')
    sparseutil.make_sparse_matrix(
        df['citee_paper_id'], df['citor_paper_id'], n_papers,
        path / 'citee2citor-indptr.bin', path / 'citee2citor-indices.bin')


def save_authorships(df, n_papers, n_authors, path):
    print('sa1')
    sparseutil.make_sparse_matrix(
        df['paper_id'], df['author_id'], n_papers,
        path / 'paper2author-indptr.bin', path / 'paper2author-indices.bin')
    print('sa2')
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

    # papers_df = load_papers_df(papers_path)
    # save_paper_years_inplace(papers_df)
    # make_mag_id_index_inplace(papers_df, 'paper_id', 'new_paper_id')
    # with open(out_path / 'papers-index.pkl', 'wb') as f:
    #     pickle.dump(papers_df, f)
    # print('unpickling papers')
    # with open(out_path / 'papers-index.pkl', 'rb') as f:
    #     papers_df = pickle.load(f)
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

    print('loading authorships')
    authorships_df = load_authorships_df(authorships_path)
    
    print('unpickling papers')
    with open(out_path / 'papers-index.pkl', 'rb') as f:
        papers_df = pickle.load(f)
    n_papers = len(papers_df)
    print('replacing1')
    replace_ids_inplace(authorships_df, 'paper_id', papers_df['new_paper_id'])
    del papers_df  # Free memory

    # authors_df = load_authors_df(authors_path)
    # make_mag_id_index_inplace(authors_df, 'author_id', 'new_author_id')
    # with open(out_path / 'authors-index.pkl', 'wb') as f:
    #     pickle.dump(authors_df, f)

    # print('unpickling authorships')
    # with open(out_path / 'authorships-table.pkl', 'rb') as f:
    #     authorships_df = pickle.load(f)

    print('unpickling authors')
    with open(out_path / 'authors-index.pkl', 'rb') as f:
        authors_df = pickle.load(f)
    n_authors = len(authors_df)
    print('replacing2')
    replace_ids_inplace(authorships_df, 'author_id', authors_df['new_author_id'])
    del authors_df  # Free memory
    print('pickling authorships')
    try:
        with open(out_path / 'authorships-table.pkl', 'wb') as f:
            pickle.dump(authorships_df, f, pickle.HIGHEST_PROTOCOL)
    except Exception:
        breakpoint()
    print('saving authorships')
    save_authorships(authorships_df, n_papers, n_authors, out_path)
    del authorships_df


def main():
    get_dataset('/data/u1033719/graph/mag-2019-11-08/', 'bingraph')
