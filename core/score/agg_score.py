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
    'self_cite': np.all,
    'coauthor': np.any,
    'influenced_tot': np.nansum,
    'influencing_tot': np.nansum,
    }

SCORE_PREC = 5

def agg_score_df(
        influence_df, coauthors=set([]), ratio_func=np.subtract,
        sort_func=np.maximum):
    """ Aggregates the scoring generated from ES paper information values.
    """

    print('\n---\n{} start score generation'.format(datetime.now()))
    if influence_df.empty:
        return pd.DataFrame(columns=FINAL_COLS)

    t1 = datetime.now()
    # Remove year column
    score_df = influence_df[SCORE_COLS]

    # Rename influence names
    score_df.rename(index=str, columns=INF_RENAME, inplace=True)

    # Create influence values for self citation
    t2 = datetime.now()
    # Aggregate scores up
    score_df = score_df.groupby(AGG_COLS).agg(AGG_FUNC).reset_index()

    score_df.loc[~score_df.self_cite, 'influenced_nsc'] = score_df.influenced_tot
    score_df.loc[~score_df.self_cite, 'influencing_nsc'] = score_df.influencing_tot
    score_df.loc[~score_df.coauthor, 'influenced_nca'] = score_df.influenced_tot
    score_df.loc[~score_df.coauthor, 'influencing_nca'] = score_df.influencing_tot
    score_df.loc[~score_df.coauthor, 'influenced_nscnca'] = score_df.influenced_nsc
    score_df.loc[~score_df.coauthor, 'influencing_nscnca'] = score_df.influencing_nsc

    t3 = datetime.now()
    # Fill nan values to zero
    score_df['influenced_nca']  = score_df['influenced_nca'].fillna(0)
    score_df['influencing_nca'] = score_df['influencing_nca'].fillna(0)
    score_df['influenced_nscnca']  = score_df['influenced_nscnca'].fillna(0)
    score_df['influencing_nscnca'] = score_df['influencing_nscnca'].fillna(0)

    t4 = datetime.now()
    # Limit precision of scoring
    score_df['influenced_tot']  = score_df.influenced_tot.round(SCORE_PREC)
    score_df['influencing_tot'] = score_df.influencing_tot.round(SCORE_PREC)
    score_df['influenced_nsc']  = score_df.influenced_nsc.round(SCORE_PREC)
    score_df['influencing_nsc'] = score_df.influencing_nsc.round(SCORE_PREC)
    score_df['influenced_nca']  = score_df.influenced_nca.round(SCORE_PREC)
    score_df['influencing_nca'] = score_df.influencing_nca.round(SCORE_PREC)
    score_df['influenced_nscnca']  = score_df.influenced_nscnca.round(SCORE_PREC)
    score_df['influencing_nscnca'] = score_df.influencing_nscnca.round(SCORE_PREC)

    t5 = datetime.now()

    # print("agg_score_df")
    # print("t1", t2-t1)
    # print("t2", t3-t2)
    # print("t3", t4-t3)
    # print("t4", t5-t4)

    print('{} finish score generation\n---'.format(datetime.now()))

    return score_df

def post_agg_score_df(score_df, ratio_func=np.subtract):
    """ Post column calculation after aggregation and filtering.
    """
    score_df.loc[:,'sum'] = score_df.influenced + score_df.influencing
    score_df.loc[:,'ratio'] = ratio_func(
        score_df.influencing, score_df.influenced)/score_df['sum']
    score_df.loc[:,'ratio'].replace([np.inf, -np.inf], 0, inplace=True)

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
