import sqlite3
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from mkAff import getAuthor
from entity_type import *
from flower_helpers import *
from influence_weight import get_weight

# Config setup
from config import *

def gen_pred_score_df(data_df):
    res = list()
    # split data info citing and cited
    for citing, info_df in data_df.groupby('citing'):
        if citing:
            s = '_citing'
        else:
            s = '_cited'

        # Group by scoring paper
        df = info_df.groupby('paper' + s).agg(lambda x : x.tolist()).reset_index()
        df['citing'] = bool(citing)
        for entity in Entity_type:
            df[entity.prefix + '_self_cite'] = df[entity.prefix + '_self_cite'].apply(lambda x : x[0])

        res.append(df)

    return pd.concat(res)

# Creates dictionaries for the weight scores
def generate_scores(conn, e_map, data_df, inc_self=False, unique=False):
    print('{} start score generation\n---'.format(datetime.now()))

    # Concat the tables together
    df = gen_pred_score_df(pd.concat(data_df.values()))

    # Check self citations
    if not inc_self:
        df = df.loc[-df[e_map.get_center_prefix() + '_self_cite'].fillna(False)]

    id_query_map = lambda f : ' '.join(f[0][1].split())
    id_to_name = dict([(tname, dict()) for tname in e_map.keyn])

    res = {'influencing' : dict(), 'influenced': dict()}
    
    cur = conn.cursor()

    for i, row in df.iterrows():
        # Determine if influencing or influenced score
        if row['citing']:
            dict_type = 'influenced'
            func = lambda x : x + '_citing'
        else:
            dict_type = 'influencing'
            func = lambda x : x + '_cited'

        # Scoring depending if an entity can only score once per paper (take max)
        if unique:
            # Check each type
            for id__type, name_type in zip(e_map.ids, e_map.keyn):
                name_col = func(name_type)
                # Make a small dataframe with influence and name to do a group by name
                row_df = pd.concat([pd.Series(row['influence'], name='influence'), pd.Series(row[name_col], name=name_col)], axis=1)
                for entity_name, score_df in row_df.groupby(name_col):
                    if entity_name == None:
                        continue
                    try:
                        res[dict_type][entity_name] += score_df['influence'].max()
                    except KeyError:
                        res[dict_type][entity_name] = score_df['influence'].max()
        else:
            # Check each type
            for id_names in map_type.keyn:
                # Add score for each series of type
                for influence, entity_name in zip(row['influence'], row[func(id_names)]):
                    if entity_name == None:
                        continue
                    try:
                        res[dict_type][entity_name] += influence
                    except KeyError:
                        res[dict_type][entity_name] = influence

    print('{} finish score generation\n---'.format(datetime.now()))
    return res

# Generates pandas dataframe for scores
def generate_score_df(influence_dict, coauthors=set([]), ratio_func=np.vectorize(lambda x, y : x / y), sort_func=np.maximum):
    df_dict = list()

    # Turn influence dictionaries into an outer merged table
    for tkey, data_dict in influence_dict.items():
        df_dict.append(pd.DataFrame.from_records(list(data_dict.items()), columns=['entity_id', tkey]))
    score_df = pd.merge(*df_dict, how='outer', on='entity_id', sort=False)

    # calculate minimum scores to fill nan values (for ratio)
    nan_influenced = score_df['influenced'].min() / 2
    nan_influencing = score_df['influenced'].min() / 2

    score_df['influenced'].fillna(nan_influenced, inplace=True)
    score_df['influencing'].fillna(nan_influencing, inplace=True)

    # calculate sum
    score_df['sum'] = score_df['influenced'] + score_df['influencing']

    # calculate influence ratios
    score_df['ratio'] = ratio_func(score_df['influenced'], score_df['influencing'])

    # sort by union max score
    score_df = score_df.assign(tmp = sort_func(score_df['influencing'], score_df['influenced']))
    score_df = score_df.sort_values('tmp', ascending=False).drop('tmp', axis=1)

    # Flag coauthors
    score_df['coauthor'] = score_df.apply(lambda row : row['entity_id'] in coauthors, axis=1)

    return score_df

def generate_coauthors(e_map, data_df):
    coauthors = list()

    # Split into cases of citing and cited
    for citing, info_df in pd.concat(data_df.values()).groupby('citing'):
        if citing:
            s = '_cited'
        else:
            s = '_citing'

        # Find coauthoring for each type of leaf
        for key in e_map.keyn:
            coauthors += info_df[key + s].tolist()

    return set(coauthors)
