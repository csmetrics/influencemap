"""
Aggregates scoring tables in elastic to be turned into a graph.

date:   25.06.18
author: Alexander Soen
"""

import pandas as pd
import numpy as np
from datetime import datetime

INF_RENAME = {
    'influenced': 'influenced_tot',
    'influencing': 'influencing_tot',
}

FINAL_COLS = [
    'entity_name', 'influenced', 'influencing', 'sum', 'ratio', 'coauthor',
    'self_cite',
    ]

SCORE_COLS = [
    'entity_name', 'influenced', 'influencing', 'self_cite', 'coauthor',
    ]

AGG_COLS = [
    'entity_name',
    ]

AGG_FUNC = {
    'coauthor': np.any,
    'influenced_tot': np.nansum,
    'influencing_tot': np.nansum,
    'influenced_nsc': np.nansum,
    'influencing_nsc': np.nansum,
    }

SCORE_PREC = 5

def safe_ratio(ratio_func, inf_type, row):

    if row['sum_{}'.format(inf_type)] == 0:
        return 0

    ratio = ratio_func(
        row['influencing_{}'.format(inf_type)],
        row['influenced_{}'.format(inf_type)])
    
    ratio /= row['sum_{}'.format(inf_type)]
    return ratio

def agg_score_df(
        influence_df, coauthors=set([]), ratio_func=np.subtract,
        sort_func=np.maximum):
    """ Aggregates the scoring generated from ES paper information values.
    """

    print('\n---\n{} start score generation'.format(datetime.now()))
    if influence_df.empty:
        return pd.DataFrame(columns=FINAL_COLS)

    # Remove year column
    score_df = influence_df[SCORE_COLS]

    # Rename influence names
    score_df.rename(index=str, columns=INF_RENAME, inplace=True) 

    # Create influence values for self citation
    score_df.loc[~score_df.self_cite, 'influenced_nsc'] = score_df.influenced_tot
    score_df.loc[~score_df.self_cite, 'influencing_nsc'] = score_df.influencing_tot

    # Aggregate scores up
    score_df = score_df.groupby(AGG_COLS).agg(AGG_FUNC).reset_index()

    score_df.loc[~score_df.coauthor, 'influenced_nca'] = score_df.influenced_tot
    score_df.loc[~score_df.coauthor, 'influencing_nca'] = score_df.influencing_tot
    score_df.loc[~score_df.coauthor, 'influenced_nscnca'] = score_df.influenced_nsc
    score_df.loc[~score_df.coauthor, 'influencing_nscnca'] = score_df.influencing_nsc

    # Fill nan values to zero
    score_df['influenced_nca']  = score_df['influenced_nca'].fillna(0)
    score_df['influencing_nca'] = score_df['influencing_nca'].fillna(0)
    score_df['influenced_nscnca']  = score_df['influenced_nscnca'].fillna(0)
    score_df['influencing_nscnca'] = score_df['influencing_nscnca'].fillna(0)

    # Limit precision of scoring
    score_df['influenced_tot']  = score_df.influenced_tot.round(SCORE_PREC)
    score_df['influencing_tot'] = score_df.influencing_tot.round(SCORE_PREC)
    score_df['influenced_nsc']  = score_df.influenced_nsc.round(SCORE_PREC)
    score_df['influencing_nsc'] = score_df.influencing_nsc.round(SCORE_PREC)
    score_df['influenced_nca']  = score_df.influenced_nca.round(SCORE_PREC)
    score_df['influencing_nca'] = score_df.influencing_nca.round(SCORE_PREC)
    score_df['influenced_nscnca']  = score_df.influenced_nscnca.round(SCORE_PREC)
    score_df['influencing_nscnca'] = score_df.influencing_nscnca.round(SCORE_PREC)

    # calculate sum
    score_df['sum_tot'] = score_df.influenced_tot + score_df.influencing_tot
    score_df['sum_nsc'] = score_df.influenced_nsc + score_df.influencing_nsc
    score_df['sum_nca'] = score_df.influenced_nca + score_df.influencing_nca
    score_df['sum_nscnca'] = score_df.influenced_nscnca + score_df.influencing_nscnca

    # calculate influence ratios
    score_df['ratio_tot'] = score_df.apply(
        lambda r: safe_ratio(ratio_func, 'tot', r), axis=1)

    score_df['ratio_nsc'] = score_df.apply(
        lambda r: safe_ratio(ratio_func, 'nsc', r), axis=1)

    score_df['ratio_nca'] = score_df.apply(
        lambda r: safe_ratio(ratio_func, 'nca', r), axis=1)

    score_df['ratio_nscnca'] = score_df.apply(
        lambda r: safe_ratio(ratio_func, 'nscnca', r), axis=1)

    print('{} finish score generation\n---'.format(datetime.now()))

    return score_df


def select_node_info(influence_df, node_names, num_papers=3):

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
