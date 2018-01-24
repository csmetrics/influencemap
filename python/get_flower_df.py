import pickle
import sqlite3
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from flower_helpers import is_self_cite
from entity_type import *
from influence_weight import get_weight

# Config setup
from config import *

REF_LABELS = ['citing', 'paper_citing', 'rc_citing', 'paper_cited']
INFO_COLS = ['auth_id', 'auth_name', 'auth_count', 'conf_id', 'conf_abv', 'conf_name', 'journ_id', 'journ_name', 'affi_id', 'affi_name']
SC_COLS = [e.eid + '_citing' for e in Entity_type] + [e.eid + '_cited' for e in Entity_type]

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

# Filter info table for papers in paper_ids
def gen_info_df(conn, paper_ids):
    cur = conn.cursor()

    total_papers = len(paper_ids)
    total_prog = 0

    paper_chunks = [paper_ids[x:x+BATCH_SIZE] for x in range(0, total_papers, BATCH_SIZE)]
    pdict = dict()
    rows = list()

    # Find information in chunks
    for chunk in paper_chunks:
        info_query = 'SELECT paper_id, {} FROM paper_info WHERE paper_id IN ({})'.format(','.join(INFO_COLS), ','.join(['?'] * len(chunk)))

        cur.execute(info_query, chunk)
        rows += cur.fetchall()

    # Turn list of tuples into dataframe
    info_df = pd.DataFrame.from_records(rows, columns=['paper'] + INFO_COLS)

    cur.close()

    return info_df

def test_sc(row):
    citing = set(row['citing'])
    val = len(set(citing)) == 1
    return val

# joining operator to rename and combine dataframes
def combine_df(ref_df, info_df, entity_id):
    # Column names for citing and cited reference information
    citing_cols = dict([(x, x + '_citing') for x in ['paper'] + INFO_COLS])
    cited_cols = dict([(x, x + '_cited') for x in ['paper'] + INFO_COLS])

    # Calculate sc join index
    ref_df['paper_map'] = ref_df['paper_citing'] + '-' + ref_df['paper_cited']

    # Join citing information
    res = pd.merge(ref_df, info_df.rename(index=str, columns=citing_cols), on='paper_citing', sort=True)
    # Join cited information
    res = pd.merge(res, info_df.rename(index=str, columns=cited_cols), on='paper_cited', sort=True)

    # Calculate scores
    res['influence'] = res.apply(lambda x : get_weight(x), axis=1)

    # Calculate self-citations
    sc_df = res[['citing', 'paper_map'] + SC_COLS]
    sc_df = sc_df.groupby('paper_map').agg(lambda x : x.tolist()).reset_index()

    # self-cite
    sc_namer = lambda s : s + '_self_cite'
    for entity_type in Entity_type:
        sc_df[sc_namer(entity_type.prefix)] = sc_df.apply(lambda x : is_self_cite(x, entity_type.eid, entity_id), axis=1)
    sc_df = sc_df.drop(columns=['citing'] + SC_COLS)

    # Join selfcite
    res = pd.merge(res, sc_df, on='paper_map', sort=False)
    
    return res.drop(columns=['paper_map'])

def gen_combined_df(conn, my_type, entity_id, entity_ids, paper_ids):
    # If entity_id is None (theshold papers) with no caching
    if not entity_id:
        print('\n---\n{} start finding paper references for: threshold\n---'.format(datetime.now()))
        ref_df = gen_reference_df(conn, paper_ids)
        print('{} finish finding paper references for: threshold\n---'.format(datetime.now()))

        # Get the papers to find info for
        info_papers = list(set(ref_df['paper_citing'].tolist()).union(set(ref_df['paper_cited'].tolist())))

        print('{} start finding paper info for: threshold\n---'.format(datetime.now()))
        info_df = gen_info_df(conn, info_papers)
        print('{} finish finding paper info for: threshold\n---'.format(datetime.now(), entity_id))

        # Combine and deal with possible unique
        print('{} start joining dataframes\n---'.format(datetime.now()))
        res_df = combine_df(ref_df, info_df, entity_ids)
        print('{} finish joining dataframes\n---'.format(datetime.now(), entity_id))
    else:
        # Check cache for entity
        cache_path = os.path.join(DATA_CACHE, entity_id)
        try:
            res_df = pd.read_pickle(cache_path)
            print('\n---\n{} found ref cache for: {}\n---'.format(datetime.now(), entity_id))
        # If miss
        except FileNotFoundError:
            print('\n---\n{} start finding paper references for: {}\n---'.format(datetime.now(), entity_id))
            ref_df = gen_reference_df(conn, paper_ids)
            print('{} finish finding paper references for: {}\n---'.format(datetime.now(), entity_id))

            # Get the papers to find info for
            info_papers = list(set(ref_df['paper_citing'].tolist()).union(set(ref_df['paper_cited'].tolist())))

            print('{} start finding paper info for: {}\n---'.format(datetime.now(), entity_id))
            info_df = gen_info_df(conn, info_papers)
            print('{} finish finding paper info for: {}\n---'.format(datetime.now(), entity_id))

            # Combine and deal with possible unique
            print('{} start joining dataframes\n---'.format(datetime.now()))
            res_df = combine_df(ref_df, info_df, [entity_id])
            print('{} finish joining dataframes\n---'.format(datetime.now(), entity_id))

            # Cache info pickle file
            res_df.to_pickle(cache_path)
            os.chmod(cache_path, 0o777)

    return res_df

# Wraps above functions to produce a dictionary of pandas dataframes for relevent information
def gen_search_df(conn, my_type, paper_map):
    entity_ids = paper_map.keys()

    res_dict = dict()
    threshold_papers = list()

    # Go through each of the entity types the user selects
    for entity_id, paper_tuple in paper_map.items():
        paper_ids = list(map(lambda x : x[0], paper_tuple))
        if len(paper_ids) < PAPER_THRESHOLD:
            threshold_papers += paper_ids
        else:
            res_dict[entity_id] = gen_combined_df(conn, my_type, entity_id, entity_ids, paper_ids)

    # Calculate threshold values
    res_dict[None] = gen_combined_df(conn, my_type, None, entity_ids, threshold_papers)

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
