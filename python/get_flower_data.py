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

    print('{} start filtering influence\n---'.format(datetime.now()))

    # Concat the tables together
    df = gen_pred_score_df(pd.concat(data_df.values()))

    influence_list = list()
    
    for i, row in df.iterrows():
        # Filter self-citations
        if not inc_self and row[e_map.get_center_prefix() + '_self_cite']:
            continue

        # Determine if influencing or influenced score
        if row['citing']:
            func = lambda x : x + '_citing'
            score_col = lambda x : (x, 0)
        else:
            func = lambda x : x + '_cited'
            score_col = lambda x : (0, x)

        # Scoring depending if an entity can only score once per paper (take max)
        if unique:
            # Check each type
            for id__type, name_type in zip(e_map.ids, e_map.keyn):
                name_col = func(name_type)
                # Make a small dataframe with influence and name to do a group by name
                row_df = pd.concat([pd.Series(row['influence'], name='influence'), pd.Series(row[name_col], name=name_col)], axis=1)

                # Group by leaf entities
                for entity_name, score_df in row_df.groupby(name_col):
                    if entity_name == None:
                        continue

                    # Add to score list
                    influence_list.append((entity_name, row['pub_year_citing'][0]) + score_col(score_df['influence'].max()))
        else:
            # Check each type
            for id_names in e_map.keyn:
                # Add score for each series of type
                for influence, entity_name in zip(row['influence'], row[func(id_names)]):
                    if entity_name == None:
                        continue

                    # Add to score list
                    influence_list.append((entity_name, row['pub_year_citing'][0]) + score_col(influence))

    # Turn list to dataframe
    res = pd.DataFrame.from_records(influence_list, columns=['entity_id', 'influence_year', 'influenced', 'influencing'])

    print('{} finish filtering influence\n---'.format(datetime.now()))

    return res

# Generates pandas dataframe for scores
def generate_score_df(influence_df, e_map, ego, coauthors=set([]), score_year_min=None, score_year_max=None, ratio_func=np.vectorize(lambda x, y : y - x), sort_func=np.maximum):

    print('{} start score generation\n---'.format(datetime.now()))

    # Check if any range set
    if score_year_min == None and score_year_max == None:
        score_df = influence_df
    else:
        # Set minimum year if none set
        if score_year_min == None:
            score_year_min = influence_df['influence_year'].min()
        else:
            score_year_min = min(influence_df['influence_year'].max(), score_year_min)
            

        # Set maximum year if none set
        if score_year_max == None:
            score_year_max = influence_df['influence_year'].max()
        else:
            score_year_max = max(influence_df['influence_year'].min(), score_year_max)

        # Filter based on year
        score_df = influence_df[(score_year_min <= influence_df['influence_year']) & (influence_df['influence_year'] <= score_year_max)]

    # Remove year column
    score_df = score_df[['entity_id', 'influenced', 'influencing']]

    # Aggrigatge scores up
    score_df = score_df.groupby('entity_id').agg(np.sum).reset_index()

    # calculate minimum scores to fill nan values (for ratio)
    nan_influenced = score_df['influenced'].iloc[score_df['influenced'].nonzero()[0]].min() / 4
    nan_influencing = score_df['influencing'].iloc[score_df['influencing'].nonzero()[0]].min() / 4

    # Incase all zeroes
    pos_vals = [x for x in [nan_influenced, nan_influencing] if str(x) != 'nan']
    if pos_vals:
        nan_val = min(pos_vals)
    else:
        nan_val = 0.001

    # Remove zero values to remove divide by zero case
    score_df.loc[score_df['influenced'] < nan_val, 'influenced'] = nan_val
    score_df.loc[score_df['influencing'] < nan_val, 'influencing'] = nan_val

    # calculate sum
    score_df['sum'] = score_df['influenced'] + score_df['influencing']

    # calculate influence ratios
    score_df['ratio'] = ratio_func(score_df['influenced'], score_df['influencing'])

    # sort by union max score
    score_df = score_df.assign(tmp = sort_func(score_df['influencing'], score_df['influenced']))
    score_df = score_df.sort_values('tmp', ascending=False).drop('tmp', axis=1)

    # Flag coauthors
    score_df['coauthor'] = score_df.apply(lambda row : row['entity_id'] in coauthors, axis=1)

    # Filter coauthors
    #score_df = score_df.loc[~score_df['entity_id'].isin(coauthors)]

    # Add meta data
    score_df.mapping = ' to '.join([e_map.get_center_text(), e_map.get_leave_text()])
    
    # Set publication year
    score_df.date_range = '{} to {}'.format(score_year_min, score_year_max)

    score_df.ego = ego

    print('{} finish score generation\n---'.format(datetime.now()))

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
