'''
Aggregates scoring tables in elastic to be turned into a graph.

date:   25.06.18
author: Alexander Soen
'''
import pandas as pd
import numpy as np
from datetime import datetime

def agg_score_df(influence_df, coauthors=set([]), \
    ratio_func=np.vectorize(lambda x, y : y - x), sort_func=np.maximum):
    ''' Aggregates the scoring generated from ES paper information values.
    '''

    print('\n---\n{} start score generation'.format(datetime.now()))

    # Remove year column
    score_cols = ['entity_id', 'influenced', 'influencing']
    score_df   = influence_df[score_cols]

    # Aggrigatge scores up
    agg_cols = ['entity_id']
    score_df = score_df.groupby(agg_cols).agg(np.sum).reset_index()

    # calculate sum
    score_df['sum'] = score_df['influenced'] + score_df['influencing']

    # calculate influence ratios
    score_df['ratio'] = ratio_func(score_df['influenced'], score_df['influencing'])
    score_df['ratio'] = score_df['ratio'] / score_df['sum']

    # sort by union max score
    score_df = score_df.assign(tmp = sort_func(score_df['influencing'], score_df['influenced']))
    score_df = score_df.sort_values('tmp', ascending=False)

    print(score_df)
    print(score_df.head(n=25))
    score_df = score_df.drop('tmp', axis=1)

    # Default value
    score_df['coauthor'] = False

    print('{} finish score generation\n---'.format(datetime.now()))

    return score_df
