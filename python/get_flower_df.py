import pickle
import sqlite3
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from flower_helpers import is_self_cite
from entity_type import *

# Config setup
from config import *

REF_LABELS = ['citing', 'paper_citing', 'rc_citing', 'paper_cited']
INFO_COLS = ['auth_id', 'auth_name', 'auth_count', 'conf_id', 'conf_name', 'journ_id', 'journ_name', 'affi_id', 'affi_name']
MULT_COLS = [0, 7]

# Filters the paper_ref database to relevent papers and uses pandas dataframes
def gen_reference_df(conn, paper_ids):
    cur = conn.cursor()

    total_papers = len(paper_ids)
    total_prog = 0

    paper_chunks = [paper_ids[x:x+BATCH_SIZE] for x in range(0, total_papers, BATCH_SIZE)]
    rows = list()

    for chunk in paper_chunks:
        papers_citing_me_q = 'SELECT 1, paper_id, ref_count, paper_ref_id FROM paper_ref_count WHERE paper_ref_id IN ({})'.format(','.join(['?'] * len(chunk)))
        papers_cited_by_me_q = 'SELECT 0, paper_id, ref_count, paper_ref_id FROM paper_ref_count WHERE paper_id IN ({})'.format(','.join(['?'] * len(chunk)))

        cur.execute(papers_citing_me_q, chunk)
        rows += cur.fetchall()

        cur.execute(papers_cited_by_me_q, chunk)
        rows += cur.fetchall()

        total_prog += len(chunk)
        print('{} finish query of paper chunk, total prog: {:.2f}%, papers: {}'.format(datetime.now(), total_prog/total_papers * 100, total_prog))

    ref_df = pd.DataFrame.from_records(rows, columns=REF_LABELS)

    cur.close()

    return ref_df


def gen_info_df(conn, paper_ids):
    cur = conn.cursor()

    total_papers = len(paper_ids)
    total_prog = 0

    paper_chunks = [paper_ids[x:x+BATCH_SIZE] for x in range(0, total_papers, BATCH_SIZE)]
    pdict = dict()
    rows = list()

    for chunk in paper_chunks:
        info_query = 'SELECT paper_id, {} FROM paper_info WHERE paper_id IN ({})'.format(','.join(INFO_COLS), ','.join(['?'] * len(chunk)))

        cur.execute(info_query, chunk)
        for row in cur.fetchall():
            paper_id, info = row[0], row[1:]
            try:
                pdict[paper_id].append(info) 
            except KeyError:
                pdict[paper_id] = [info]

    for paper_id, info_tuples in pdict.items():
        row = (paper_id, )
        # Combine information of same paper
        list_info = list(map(list, zip(*info_tuples)))

        # Change type of lists to strings for hashing
        for i in range(len(INFO_COLS)):
            if i-1 in MULT_COLS:
                continue
            elif i in MULT_COLS:
                ids = list(map(str, list_info[i]))
                names = list(map(str, list_info[i+1]))

                idx = np.argsort(ids)

                sorted_ids = np.array(ids)[idx]
                sorted_names = np.array(names)[idx]

                # Change input into a string for hashing
                row += (','.join(sorted_ids), ','.join(sorted_names))
            else:
                row += (list_info[i][0], )

        rows.append(row)

    # Turn list of tuples into dataframe
    info_df = pd.DataFrame.from_records(rows, columns=['paper'] + INFO_COLS)

    cur.close()

    return info_df

# joining operator to rename and combine dataframes
def combine_df(ref_df, info_df):
    # Column names for citing and cited reference information
    citing_cols = dict([(x, x + '_citing') for x in ['paper'] + INFO_COLS])
    cited_cols = dict([(x, x + '_cited') for x in ['paper'] + INFO_COLS])
    
    res = pd.merge(ref_df, info_df.rename(index=str, columns=citing_cols), on='paper_citing', sort=False)
    res = pd.merge(res, info_df.rename(index=str, columns=cited_cols), on='paper_cited', sort=False)
    
    return res

# Wraps above functions to produce a dictionary of pandas dataframes for relevent information
def gen_search_df(conn, paper_map, etype):
    res_dict = dict()
    threshold_papers = list()
    entity_ids = paper_map.keys()

    for entity_id, paper_ids in paper_map.items():
        if len(paper_ids) < PAPER_THRESHOLD:
            threshold_papers += paper_ids
        else:
            # CHECK CACHE
            cache_path = os.path.join(DATA_CACHE, entity_id)
            try:
                res_dict[entity_id] = pd.read_pickle(cache_path)
                print(res_dict[entity_id])
                print('\n---\n{} found cache data for: {}\n---'.format(datetime.now(), entity_id))
            except FileNotFoundError:
                # IF MISS
                print('\n---\n{} start finding paper references for: {}\n---'.format(datetime.now(), entity_id))
                ref_df = gen_reference_df(conn, paper_ids)
                print('{} finish finding paper references for: {}\n---'.format(datetime.now(), entity_id))

                print('{} start finding paper info for: {}\n---'.format(datetime.now(), entity_id))
                info_df = gen_info_df(conn, paper_ids)
                print('{} finish finding paper info for: {}\n---'.format(datetime.now(), entity_id))

                print('{} start joining dataframes for: {}\n---'.format(datetime.now(), entity_id))
                e_df = combine_df(ref_df, info_df)
                res_dict[entity_id] = e_df
                print('{} finish joining dataframes for: {}\n---'.format(datetime.now(), entity_id))

                # Cache pickle file
                e_df.to_pickle(cache_path)
                os.chmod(cache_path, 0o777)

    # deal with threshold papers
    print('\n---\n{} start finding paper references for: threshold\n---'.format(datetime.now()))
    e_df = gen_reference_df(conn, threshold_papers)
    print('{} finish finding paper references for: threshold\n---'.format(datetime.now()))

    print('{} start finding paper info for: threshold\n---'.format(datetime.now()))
    info_df = gen_info_df(conn, threshold_papers)
    print('{} finish finding paper info for: threshold\n---'.format(datetime.now(), entity_id))

    # Other entities
    print('{} start joining dataframes for: threshold\n---'.format(datetime.now()))
    #res_dict[None] = combine_df(ref_df, info_df)
    print('{} finish joining dataframes for: threshold\n---'.format(datetime.now(), entity_id))

    # Calculate self-citations
    is_sc_vec = np.vectorize(lambda x, y, z : is_self_cite(x, y, z, entity_ids))

    # Calculate auth self-citations if auth
    if etype == Entity.AUTH:
        for df in res_dict.values():
            if not df.empty:
                df['self_cite'] = is_sc_vec(df['citing'], df['auth_id_citing'], df['auth_id_cited'])

    # Calculate inst self-citations if inst
    elif etype == Entity.AFFI:
        for df in res_dict.values():
            if not df.empty:
                df['self_cite'] = is_sc_vec(df['citing'], df['affi_id_citing'], df['affi_id_cited'])

    return res_dict

if __name__ == "__main__":
    from mkAff import getAuthor
    import os, sys

    # input
    user_in = sys.argv[1]

    # get paper ids associated with input name
    _, id_2_paper_id, _ = getAuthor(user_in)

    conn = sqlite3.connect(DB_PATH)

    # filter_references(conn, associated_papers)
    test = gen_search_df(conn, id_2_paper_id)
#    for k, v in test.items():
#        print(v.dtypes)
        #print(k)
        #print(v)
