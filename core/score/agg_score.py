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
    score_cols = ['entity_name', 'influenced', 'influencing']
    score_df   = influence_df[score_cols]

    # Aggrigatge scores up
    agg_cols = ['entity_name']
    score_df = score_df.groupby(agg_cols).agg(np.sum).reset_index()

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


def agg_node_info(influence_df, node_names, coauthors=set([]), num_papers=3):
    '''
    '''
    # Filter out non-node data
    filtered_influence = influence_df[ influence_df['entity_name'].isin(node_names) ]

    # Node information results
    node_info = dict()

    for node_name, node_influence in filtered_influence.groupby('entity_name'):
        # Remove duplicates TODO for affiliations
        #print(node_influence.columns.values)

        info = dict()
        info['node_name'] = node_name
        #info['node_ids']  = list(set(node_influence['entity_id']))

        # Remove node ids
        remove_cols = ['entity_name', 'ego_paper_id',  #'entity_id', 
                       'influence_year', 'publication_year']
        node_influence = node_influence.drop(remove_cols, 1)

        # Add column for counting
        node_influence['influenced_count']  = node_influence['influenced']\
                                                .apply(lambda x: 1 if x > 0 else 0)
        node_influence['influencing_count'] = node_influence['influencing']\
                                                .apply(lambda x: 1 if x > 0 else 0)

        # Paper influence scores
        score_groups = ['link_paper_id', 'link_paper_title', 'link_year']
        paper_scores = node_influence.groupby(score_groups).agg(np.sum)
        
        # Get information
        info['reference_papers'] = list()
        ref_scores = paper_scores[ paper_scores['influenced'] > 0 ]
        for paper_group_info, row in ref_scores.nlargest(num_papers,
                                        'influenced').iterrows():
            paper_id, paper_title, year = paper_group_info

            paper_dict = dict()
            paper_dict['paper_title']     = paper_title
            paper_dict['paper_id']        = paper_id
            paper_dict['year']            = year
            paper_dict['influence_score'] = row['influenced']
            paper_dict['count']           = row['influenced_count']

            info['reference_papers'].append(paper_dict)

        info['citation_papers'] = list()
        cite_scores = paper_scores[ paper_scores['influencing'] > 0 ]
        for paper_group_info, row in cite_scores.nlargest(num_papers,
                                'influencing').iterrows():
            paper_id, paper_title, year = paper_group_info

            paper_dict = dict()
            paper_dict['paper_title']     = paper_title
            paper_dict['paper_id']        = paper_id
            paper_dict['year']            = year
            paper_dict['influence_score'] = row['influencing']
            paper_dict['count']           = row['influencing_count']

            info['citation_papers'].append(paper_dict)

        node_info[node_name] = info

    return node_info
