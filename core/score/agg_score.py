'''
Aggregates scoring tables in elastic to be turned into a graph.

date:   25.06.18
author: Alexander Soen
'''
import pandas as pd
import numpy as np
import copy

from datetime   import datetime
from functools  import reduce
from core.search.query_info_cache import paper_info_cache_query
from core.search.query_info       import get_paper_info_dict


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
        remove_cols = ['entity_name', #'ego_paper_id',  #'entity_id', 
                       'influence_year', 'publication_year']
        node_influence = node_influence.drop(remove_cols, 1)

        # Add column for counting
        node_influence['influenced_count']  = node_influence['influenced']\
                                                .apply(lambda x: 1 if x > 0 else 0)
        node_influence['influencing_count'] = node_influence['influencing']\
                                                .apply(lambda x: 1 if x > 0 else 0)

        # Iterate through each of the papers
        node_paper_info = list()
        for link_id, score_info in node_influence.groupby('link_paper_id'):
            info_dict = dict()

            # Score group information
            info_dict['link_id'] = link_id
            info_dict['ego_ids'] = set(score_info['ego_paper_id'])
            
            # Scores
            info_dict['influenced']  = score_info['influenced'].sum().item()
            info_dict['influencing'] = score_info['influencing'].sum().item()

            info_dict['c_influenced']  = score_info['influenced_count'].sum().item()
            info_dict['c_influencing'] = score_info['influencing_count'].sum().item()

            # Node type
            info_dict['type'] = node_type.ident

            node_paper_info.append(info_dict)

        reference_ids = sorted(node_paper_info,
                key=lambda x: -x['influenced'])[:num_papers]
        citation_ids = sorted(node_paper_info,
                key=lambda x: -x['influencing'])[:num_papers]

        # Generate the information for associated papers
        rel_paper_info = set()
        info_dicts = reference_ids + citation_ids

        rel_paper_info.update(map(lambda x: x['link_id'], info_dicts))
        ego_papers = map(lambda x: x['ego_ids'], info_dicts)
        rel_paper_info.update(reduce(lambda x, y: x.union(y), ego_papers))

        # find the map from ids to paper information
        info_papers = list()
        for rel_paper in rel_paper_info:
            info_papers.append(paper_info_cache_query(rel_paper))

        info_map = dict()
        for info_paper in info_papers:
            info_map[info_paper['PaperId']] = info_paper

        # Create info dictionaries for the nodes
        reference_info = list()
        for info_dict in reference_ids:
            # Link paper information
            link_paper_info = info_map[info_dict['link_id']]
            link_info_dict  = get_paper_info_dict(link_paper_info)

            # Ego paper information
            ego_info_dict_list = list()
            for ego_paper_id in info_dict['ego_ids']:
                ego_paper_info = info_map[ego_paper_id]
                ego_info_dict_list.append(get_paper_info_dict(ego_paper_info))

            # Delete the id fields
            new_info = copy.copy(info_dict)
            del new_info['link_id']
            del new_info['ego_ids']

            # Assign new fields for the link and egos
            new_info['link_paper'] = link_info_dict
            new_info['ego_papers'] = ego_info_dict_list

            reference_info.append(new_info)

        citation_info = list()
        for info_dict in citation_ids:
            # Link paper information
            link_paper_info = info_map[info_dict['link_id']]
            link_info_dict  = get_paper_info_dict(link_paper_info)

            # Ego paper information
            ego_info_dict_list = list()
            for ego_paper_id in info_dict['ego_ids']:
                ego_paper_info = info_map[ego_paper_id]
                ego_info_dict_list.append(get_paper_info_dict(ego_paper_info))

            # Delete the id fields
            new_info = copy.copy(info_dict)
            del new_info['link_id']
            del new_info['ego_ids']

            # Assign new fields for the link and egos
            new_info['link_paper'] = link_info_dict
            new_info['ego_papers'] = ego_info_dict_list

            citation_info.append(new_info)

        info['reference_papers'] = reference_info
        info['citation_papers']  = citation_info

        node_info[node_name] = info

    return node_info
