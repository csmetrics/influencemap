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
    if influence_df.empty:
        score_cols = ['entity_name', 'influenced', 'influencing', 'sum', 'ratio', 'coauthor']
        return pd.DataFrame(columns=score_cols)

    # Remove year column
    score_cols = ['entity_name', 'influenced', 'influencing']
    score_df   = influence_df[score_cols]

    # Aggrigatge scores up
    agg_cols = ['entity_name']
    score_df = score_df.groupby(agg_cols).agg(np.sum).reset_index()
    score_df['influenced']  = score_df['influenced'].round(decimals = 5)
    score_df['influencing'] = score_df['influencing'].round(decimals = 5)

    # calculate sum
    score_df['sum'] = score_df['influenced'] + score_df['influencing']

    # calculate influence ratios
    score_df['ratio'] = ratio_func(score_df['influenced'], score_df['influencing'])
    score_df['ratio'] = score_df['ratio'] / score_df['sum']

    # sort by union max score
    score_df = score_df.assign(tmp = sort_func(score_df['influencing'], score_df['influenced']))
    score_df = score_df.sort_values('tmp', ascending=False)

    score_df = score_df.drop('tmp', axis=1)

    # Default value
    score_df['coauthor'] = False

    print('{} finish score generation\n---'.format(datetime.now()))

    return score_df


def select_node_info(influence_df, node_names, num_papers=3):
    '''
    '''
    influence_cols = ['influenced', 'influencing', 'link_paper_id', 'ego_paper_id']
    node_cols = ['entity_name', 'entity_type']

    # Filter out non-node data
    filtered_influence = influence_df[ \
            influence_df['entity_name'].isin(node_names) ]
    filtered_influence = filtered_influence[ influence_cols + node_cols ]

    # Node information results
    node_info = dict()

    for entity_info, node_influence in filtered_influence.groupby(node_cols):
        info = dict()
        node_name, node_type = entity_info
        info['node_name'] = node_name

        # Get the aggregate influence and influencing
        paper_scores = node_influence.groupby('link_paper_id', \
                as_index=False).agg(\
                {'influenced': np.sum,
                 'influencing': np.sum,
                 'ego_paper_id': lambda x: tuple(x)})

        top_influenced  = paper_scores.sort_values('influenced', \
                ascending=False).head(n=num_papers)
        top_influencing = paper_scores.sort_values('influencing', \
                ascending=False).head(n=num_papers)

        info['reference_link'] = top_influenced['link_paper_id'].tolist()
        info['citation_link']  = top_influencing['link_paper_id'].tolist()

        to_sets = lambda x: list(map(lambda y: list(set(y)), x))
        info['reference_ego'] = to_sets(top_influenced['ego_paper_id'].tolist())
        info['citation_ego']  = to_sets(top_influencing['ego_paper_id'].tolist())

        print(info)

        node_info[node_name] = info

    return node_info
