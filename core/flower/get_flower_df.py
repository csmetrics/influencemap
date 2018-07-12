import pickle
import sqlite3
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from core.flower.flower_helpers import is_self_cite
from core.utils.entity_type import *
from core.utils.influence_weight import get_weight

# Config setup
from core.config import *

REF_LABELS = ['citing', 'paper_citing', 'rc_citing', 'paper_cited']
INFO_COLS = ['auth_id', 'auth_name', 'auth_count', 'conf_id', 'conf_abv', 'conf_name', 'journ_id', 'journ_name', 'affi_id', 'affi_name', 'pub_year']
SC_COLS = [e.eid + '_citing' for e in Entity_type] + [e.eid + '_cited' for e in Entity_type]

# Filters the paper_ref database to relevent papers and uses pandas dataframes
def gen_reference_df(conn, paper_ids):
    cur = conn.cursor()

    total_papers = len(paper_ids)
    total_prog = 0

    paper_chunks = [paper_ids[x:x+BATCH_SIZE] for x in range(0, total_papers, BATCH_SIZE)]
    rows = list()

    for chunk in paper_chunks:
        papers_citing_me_q = 'SELECT paper_ref_id, 1, paper_id, ref_count, paper_ref_id FROM paper_ref_count WHERE paper_ref_id IN ({})'.format(','.join(['?'] * len(chunk)))
        papers_cited_by_me_q = 'SELECT paper_id, 0, paper_id, ref_count, paper_ref_id FROM paper_ref_count WHERE paper_id IN ({})'.format(','.join(['?'] * len(chunk)))

        cur.execute(papers_citing_me_q, chunk)
        rows += cur.fetchall()

        cur.execute(papers_cited_by_me_q, chunk)
        rows += cur.fetchall()

        total_prog += len(chunk)
        print('{} finish query of paper chunk, total prog: {:.2f}%, papers: {}'.format(datetime.now(), total_prog/total_papers * 100, total_prog))

    ref_df = pd.DataFrame.from_records(rows, columns=["info_from"] + REF_LABELS)

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

# joining operator to rename and combine dataframes
def combine_df(ref_df, info_df):
    # Column names for citing and cited reference information
    citing_cols = dict([(x, x + '_citing') for x in ['paper'] + INFO_COLS] + [('info_from', 'info_from')])
    cited_cols = dict([(x, x + '_cited') for x in ['paper'] + INFO_COLS] + [('info_from', 'info_from')])

    # Calculate sc join index
    ref_df['paper_map'] = ref_df['paper_citing'] + '-' + ref_df['paper_cited']

    # Join citing information
    res = pd.merge(ref_df, info_df.rename(index=str, columns=citing_cols), on='paper_citing', sort=True)
    # Join cited information
    res = pd.merge(res, info_df.rename(index=str, columns=cited_cols), on='paper_cited', sort=True)

    return res

# generate score info from combined dataframe
def score_information(df, entity_names, ignore_papers):
    # If empty return empty
    if df.empty:
        return df

    # Remove ignored papers
    df = df[~df['info_from'].isin(ignore_papers)]

    # Calculate scores
    df['influence'] = df.apply(lambda x : get_weight(x), axis=1)

    # Calculate self-citations
    sc_df = df[['citing', 'paper_map'] + SC_COLS]
    sc_df = sc_df.groupby('paper_map').agg(lambda x : x.tolist()).reset_index()

    # self-cite
    sc_namer = lambda s : s + '_self_cite'
    for entity_type in Entity_type:
        sc_df[sc_namer(entity_type.prefix)] = sc_df.apply(lambda x : is_self_cite(x, entity_type.eid, entity_names), axis=1)
    sc_df = sc_df.drop(columns=['citing'] + SC_COLS)

    # Join selfcite
    df = pd.merge(df, sc_df, on='paper_map', sort=False)

    return df.drop(columns=['paper_map'])

# Generates combined information tables + deals with caching
def gen_combined_df(conn, entity, entity_names, paper_ids, ignore_papers):
    # If entity_name is None (theshold papers) with no caching
    if not entity:
        print('\n---\n{} start finding paper references for: threshold'.format(datetime.now()))
        ref_df = gen_reference_df(conn, paper_ids)
        print('{} finish finding paper references for: threshold\n---'.format(datetime.now()))

        # Get the papers to find info for
        info_papers = list(set(ref_df['paper_citing'].tolist()).union(set(ref_df['paper_cited'].tolist())))

        print('\n---\n{} start finding paper info for: threshold'.format(datetime.now()))
        info_df = gen_info_df(conn, info_papers)
        print('{} finish finding paper info for: threshold\n---'.format(datetime.now()))

        # Combine and deal with possible unique
        print('\n---\n{} start joining dataframes'.format(datetime.now()))
        res_df = combine_df(ref_df, info_df)
        print('{} finish joining dataframes\n---'.format(datetime.now()))
    else:
        # Check cache for entity
        cache_path = os.path.join(CACHE_DIR, entity.cache_str())
        try:
            res_df = pd.read_pickle(cache_path)
            print('\n---\n{} found ref cache for: {}\n---'.format(datetime.now(), entity.entity_name))
        # If miss
        except FileNotFoundError:
            print('\n---\n{} start finding paper references for: {}'.format(datetime.now(), entity.entity_name))
            ref_df = gen_reference_df(conn, paper_ids)
            print('{} finish finding paper references for: {}\n---'.format(datetime.now(), entity.entity_name))

            # Get the papers to find info for
            info_papers = list(set(ref_df['paper_citing'].tolist()).union(set(ref_df['paper_cited'].tolist())))

            print('\n---\n{} start finding paper info for: {}'.format(datetime.now(), entity.entity_name))
            info_df = gen_info_df(conn, info_papers)
            print('{} finish finding paper info for: {}\n---'.format(datetime.now(), entity.entity_name))

            # Combine and deal with possible unique
            print('\n---\n{} start joining dataframes'.format(datetime.now()))
            res_df = combine_df(ref_df, info_df)
            print('{} finish joining dataframes\n---'.format(datetime.now()))

            # Cache info pickle file
            res_df.to_pickle(cache_path)
            os.chmod(cache_path, 0o777)

    return score_information(res_df, entity_names, ignore_papers)

# Wraps above functions to produce a dictionary of pandas dataframes for relevent information
def gen_search_df(conn, paper_map, unselect_paper_map):
    entity_names = list(map(lambda x : x.entity_name, paper_map.keys()))

    res_dict = dict()
    threshold_papers = list()
    threshold_ignore = list()
    # Go through each of the entity types the user selects
    for entity, paper_tuple in paper_map.items():
        paper_ids = paper_tuple

        # Papers to unselect
        ignore_papers = unselect_paper_map[entity]

        # Bin entity papers with papers less than threshold number
        if len(paper_ids) < PAPER_THRESHOLD:
            threshold_papers += paper_ids
            threshold_ignore += unselect_paper_map[entity]
        else:
            res_dict[entity.name_str()] = gen_combined_df(conn, entity, entity_names, paper_ids, ignore_papers)

    # Calculate threshold values
    res_dict[None] = gen_combined_df(conn, None, entity_names, threshold_papers, threshold_ignore)

    return res_dict
