import sqlite3
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

# Generates pandas dataframe for scores
def generate_score_df(influence_df, e_map, ego, coauthors=set([]), score_year_min=None, score_year_max=None, ratio_func=np.vectorize(lambda x, y : y - x), sort_func=np.maximum):

    print('\n---\n{} start score generation'.format(datetime.now()))

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
