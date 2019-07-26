'''
'''

import pandas as pd
import networkx as nx
import numpy as np
from datetime import datetime

# Config setup
from core.config import *

def normalise_singular_linear(series):
    ''' Function to normalise data for a singular series
    '''
    max_val = series.max()
    min_val = series.min()

    max_min_dif = max_val - min_val

    # Cases if max equal to min
    if max_min_dif == 0:
        series = min_val
        return series

    # Normalise
    return series.apply(lambda x : (x - min_val) / max_min_dif)

def normalise_to_proportion_of_max(series):
    ''' Function to normalise node sizes with max node being 1
    '''
    max_val = series.max()
    return series.apply(lambda x: x/max_val)

def normalise_colour_dif(series):
    ''' Function to normalise color
    '''
    max_val = series.max()
    min_val = series.min()

    normalisation = max(abs(max_val), abs(min_val))

    # Cases if max equal to min
    if normalisation == 0:
        series = 0.5
        return series

    # Normalise
    return series.apply(lambda x : (x + normalisation) / (2 * normalisation))

def normalise_double_log(series1, series2):
    ''' Normalise two series logwise
    '''
    max_val = max(series1.max(), series2.max())
    # min_val = min(series1.min(), series2.min())
    min_val = 0

    max_min_dif = max_val - min_val

    # Cases if max equal to min
    if max_min_dif == 0 and max_val == 0:
        return series1, series2
    elif max_min_dif == 0:
        return pd.Series([1] * series.size), pd.Series([1] * series.size)

    # Scale from 1 to 1024
    scaled1 = series1.apply(lambda x : 1 + (x - min_val) / max_min_dif)
    scaled2 = series2.apply(lambda x : 1 + (x - min_val) / max_min_dif)

    # Log down to 0 to 1
    return scaled1.apply(np.log2), scaled2.apply(np.log2)

def score_df_to_graph(score_df):
    ''' Turns the dataframe for flower into networkx graph.
        Additionally normalises influence values.
    '''

    print('\n---\n{} start graph generation'.format(datetime.now()))

    # Ego Graph
    egoG = nx.DiGraph(
        ego='ego', max_influenced=score_df['influenced'].max(),
        max_influencing=score_df['influencing'].max())

    # Normalise values
    score_df.loc[:,'normed_sum'] = normalise_to_proportion_of_max(score_df['sum'])
    score_df.loc[:,'normed_ratio'] = normalise_colour_dif(score_df['ratio'])

    norm_influenced, norm_influencing = normalise_double_log(
        score_df['influenced'], score_df['influencing'])

    score_df.loc[:,'normed_influenced'] = norm_influenced
    score_df.loc[:,'normed_influencing'] = norm_influencing
    score_df.loc[:,'dif'] = score_df['influencing'] - score_df['influenced']

    # Add ego
    egoG.add_node('ego', name=score_df.ego, weight=None)

    # Iterate over dataframe
    for _, row in score_df.iterrows():
        # Add ratio weight
        egoG.add_node(
            row['entity_name'], nratiow=row['normed_ratio'],
            ratiow=row['ratio'], sumw=row['normed_sum'], sum=row['sum'],
            coauthor=row['coauthor'], dif=row['dif'],
            inf_in=row['influenced'], inf_out=row['influencing'],
            bloom_order=row['bloom_order'])

        # Add influence weights
        egoG.add_edge(
            row['entity_name'], 'ego', weight=row['influencing'],
            nweight=row['normed_influencing'], direction='out',
            ratiow=row['ratio'], dif=row['dif'], sumw=row['normed_sum'],
            inf_in=row['influenced'], inf_out=row['influencing'],
            bloom_order=row['bloom_order'])
        egoG.add_edge(
            'ego', row['entity_name'], weight=row['influenced'],
            nweight=row['normed_influenced'], direction='in',
            ratiow=row['ratio'], dif=row['dif'], sumw=row['normed_sum'],
            inf_in=row['influenced'], inf_out=row['influencing'],
            bloom_order=row['bloom_order'])

    print('{} finish graph generation\n---'.format(datetime.now()))

    return egoG
