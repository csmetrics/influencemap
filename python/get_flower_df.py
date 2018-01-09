import pickle
import sqlite3
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from flower_helpers import is_selfcite

# Config setup
from config import *

REF_LABELS = ['citing', 'citing_paper', 'citing_rc', 'cited_paper']
INFO_COLS = ['auth_id', 'auth_count', 'conf_id', 'journ_id', 'affi_id']
MULT_COLS = [0]

# Filters the paper_ref database to relevent papers and uses pandas dataframes
def gen_reference_df(conn, paper_ids):
    cur = conn.cursor()

    # NEED TO CACHE THIS
    auth_cache_dict = dict()
    is_sc_vec = np.vectorize(lambda x, y: is_selfcite(conn, x, y, auth_cache_dict), otypes=[bool])

    total_papers = len(paper_ids)
    total_prog = 0

    paper_chunks = [paper_ids[x:x+BATCH_SIZE] for x in range(0, total_papers, BATCH_SIZE)]
    rows = list()

    for chunk in paper_chunks:
        papers_citing_me_q = 'SELECT 1, paper_id, paper_rc, paper_ref_id FROM paper_ref_count WHERE paper_ref_id IN ({})'.format(','.join(['?'] * len(chunk)))
        papers_cited_by_me_q = 'SELECT 0, paper_id, paper_rc, paper_ref_id FROM paper_ref_count WHERE paper_id IN ({})'.format(','.join(['?'] * len(chunk)))

        cur.execute(papers_citing_me_q, chunk)
        rows += cur.fetchall()

        cur.execute(papers_cited_by_me_q, chunk)
        rows += cur.fetchall()

        total_prog += len(chunk)
        print('{} finish query of paper chunk, total prog: {:.2f}%, papers: {}'.format(datetime.now(), total_prog/total_papers * 100, total_prog))

    ref_df = pd.DataFrame.from_records(rows, columns=REF_LABELS)

    # calculate self citation row
    ref_df['self_cite'] = is_sc_vec(ref_df['citing_paper'], ref_df['cited_paper'])

    return ref_df

# Generates paper_info from database into pandas format
def get_paper_info(conn, paper_id):
    info_query = 'SELECT {} FROM paper_info WHERE paper_id = ?'.format(','.join(INFO_COLS))

    cur = conn.cursor()
    cur.execute(info_query, (paper_id, ))
    res = [set() for i in range(len(INFO_COLS))]
    for line in cur.fetchall():
        for i, val in enumerate(line):
            res[i].add(val)
    cur.close()
    res_gen = (pd.Series(list(val)) if i in MULT_COLS else next(iter(val)) for i, val in enumerate(res))
    return tuple(res_gen)

# Expands the ref dataframe to include more information on papers
def gen_info_df(conn, ref_df):
    if not ref_df.empty:
        citing_cols = map(lambda s : 'citing_' + s, INFO_COLS)
        temp = list(zip(*ref_df['citing_paper'].map(lambda p : get_paper_info(conn, p))))
        for i, c in enumerate(citing_cols):
            ref_df[c] = temp[i]

        cited_cols = map(lambda s : 'cited_' + s, INFO_COLS)
        temp = list(zip(*ref_df['cited_paper'].map(lambda p : get_paper_info(conn, p))))
        for i, c in enumerate(cited_cols):
            ref_df[c] = temp[i]

    else:
        print('EMPTY!')
    return ref_df

# Wraps above functions to produce a dictionary of pandas dataframes for relevent information
def gen_search_df(conn, paper_map):
    res_dict = dict()
    threshold_papers = list()

    for entity_id, paper_ids in paper_map.items():
        if len(paper_ids) < PAPER_THRESHOLD:
            threshold_papers += paper_ids
        else:
            # CHECK CACHE
            cache_path = os.path.join(DATA_CACHE, entity_id)
            try:
                res_dict[entity_id] = pd.read_pickle(cache_path)
                print('\n---\n{} found cache data for: {}\n---'.format(datetime.now(), entity_id))
            except FileNotFoundError:
                # IF MISS
                print('\n---\n{} start finding paper references for: {}\n---'.format(datetime.now(), entity_id))
                e_df = gen_reference_df(conn, paper_ids)
                print('{} finish finding paper references for: {}\n---'.format(datetime.now(), entity_id))

                print('{} start finding paper info for: {}\n---'.format(datetime.now(), entity_id))
                e_df = gen_info_df(conn, e_df)
                print('{} finish finding paper info for: {}\n---'.format(datetime.now(), entity_id))

                res_dict[entity_id] = e_df

                # Cache pickle file
                e_df.to_pickle(cache_path)
                os.chmod(cache_path, 0o777)

    # deal with threshold papers
    print('\n---\n{} start finding paper references for: threshold\n---'.format(datetime.now()))
    e_df = gen_reference_df(conn, threshold_papers)
    print('{} finish finding paper references for: threshold\n---'.format(datetime.now()))

    print('{} start finding paper info for: threshold\n---'.format(datetime.now()))
    e_df = gen_info_df(conn, e_df)
    print('{} finish finding paper info for: threshold\n---'.format(datetime.now(), entity_id))

    res_dict[None] = e_df

    return res_dict

if __name__ == "__main__":
    from mkAff import getAuthor
    import os, sys

    # input
    user_in = sys.argv[1]

    # get paper ids associated with input name
    _, id_2_paper_id = getAuthor(user_in)

    conn = sqlite3.connect(DB_PATH)

    # filter_references(conn, associated_papers)
    test = gen_search_df(conn, id_2_paper_id)
#    for k, v in test.items():
#        print(v.dtypes)
        #print(k)
        #print(v)
