'''
Aggregates scoring tables in elastic to be turned into a graph.

date:   25.06.18
author: Alexander Soen
'''
import pandas as pd
import numpy as np
from datetime import datetime

def agg_score_df(influence_df, coauthors=set([]), \
    score_year_min=None, score_year_max=None, \
    ratio_func=np.vectorize(lambda x, y : y - x), sort_func=np.maximum):
    ''' Aggregates the scoring generated from ES paper information values.
    '''

    print('\n---\n{} start score generation'.format(datetime.now()))

    # Check if any range set
    if score_year_min == None and score_year_max == None:
        score_df = influence_df
    else:
        no_nan_date = influence_df[ influence_df['influence_date'].notna() ]

        # Set minimum year if none set
        if score_year_min == None:
            score_date_min = no_nan_date['influence_date'].min()
        else:
            score_date_min = min(no_nan_date['influence_date'].max(),\
                score_year_min)
            

        # Set maximum year if none set
        if score_year_max == None:
            score_date_max = no_nan_date['influence_date'].max()
        else:
            score_date_max = max(no_nan_date['influence_date'].min(),\
                score_year_max)

        # Filter based on year
        score_df = no_nan_date[(score_date_min <= \
            no_nan_date['influence_date']) & \
            (no_nan_date['influence_date'] <= score_date_max)]

    # Remove year column
    score_cols = ['entity_id', 'influenced', 'influencing']
    score_df   = score_df[score_cols]

    # Aggrigatge scores up
    agg_cols = ['entity_id']
    score_df = score_df.groupby(agg_cols).agg(np.sum).reset_index()

    # calculate sum
    score_df['sum'] = score_df['influenced'] + score_df['influencing']

    # calculate influence ratios
    score_df['ratio'] = ratio_func(score_df['influenced'], score_df['influencing'])

    # sort by union max score
    score_df = score_df.assign(tmp = sort_func(score_df['influencing'], score_df['influenced']))
    score_df = score_df.sort_values('tmp', ascending=False).drop('tmp', axis=1)

    # Flag coauthors TODO FIX
    score_df['coauthor'] = False

    print('{} finish score generation\n---'.format(datetime.now()))

    return score_df
