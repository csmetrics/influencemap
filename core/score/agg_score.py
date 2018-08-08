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

    for entity_info, node_influence in filtered_influence.groupby(['entity_name', 'entity_type']):
        info = dict()
        node_name, node_type = entity_info
        info['node_name'] = node_name

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

        # Iterate through each of the papers
        node_paper_info = list()
        for score_group, score_info in node_influence.groupby(score_groups):
            info_dict = dict()

            # Score group information
            link_id, link_title, link_year = score_group
            #info_dict['link_id']    = link_id
            info_dict['link_title'] = link_title
            info_dict['link_year']  = link_year.item()
            
            # Scores
            info_dict['influenced']  = score_info['influenced'].sum().item()
            info_dict['influencing'] = score_info['influencing'].sum().item()

            #info_dict['count'] = score_info['influenced_count'].sum().item()

            # Link paper information
            info_dict['link_auth'] = list(set(score_info['AuthorName']))
            info_dict['link_affi'] = list(set(score_info['AffiliationName']))
            info_dict['link_conf'] = list(set(score_info['ConferenceName']))
            info_dict['link_jour'] = list(set(score_info['JournalName']))

            # Ego paper
            info_dict['ego_title'] = list(set(score_info['ego_paper_title']))

            # Node type
            info_dict['type'] = node_type.ident

            node_paper_info.append(info_dict)

        info['reference_papers'] = sorted(node_paper_info,
                key=lambda x: -x['influenced'])[:num_papers]
        info['citation_papers'] = sorted(node_paper_info,
                key=lambda x: -x['influencing'])[:num_papers]

        node_info[node_name] = info

    return node_info
