'''
Flower functions for node information.
'''

import numpy as np
from datetime import datetime


def select_node_info(influence_df, node_names):
    ''' Determine node information through single pass through dataframe.
    '''
    influence_cols = ['influenced', 'influencing', 'link_paper_id', 'ego_paper_id', 'publication_year']
    node_cols = ['entity_name', 'entity_type']

    # Filter out non-node data
    filtered_influence = influence_df[ influence_df['entity_name'].isin(node_names) ]
    filtered_influence = filtered_influence[ influence_cols + node_cols ]
    filtered_influence['is_ref'] = filtered_influence['influenced'] > 0
    filtered_influence['is_cit'] = filtered_influence['influencing'] > 0

    # Node information results
    node_info = dict()
    for iterrow in filtered_influence.iterrows():
        _, row = iterrow
        entity_name    = row['entity_name']
        entity_type    = row['entity_type']
        ego_paper_id   = row['ego_paper_id']
        ego_paper_year = row['publication_year']
        link_paper_id  = row['link_paper_id']
        
        # Set default dictionaries
        info = node_info.setdefault(entity_name, { 'paper_list': dict(), 'type': entity_type.ident })
        paper_info = info['paper_list'].setdefault(ego_paper_id, { 'year': int(ego_paper_year), 'ego_paper': int(ego_paper_id), 'reference': set(), 'citation': set() })

        # Determine if reference or citation
        if row['is_ref']:
            paper_info['reference'].add(link_paper_id)
        if row['is_cit']:
            paper_info['citation'].add(link_paper_id)

    # Turn paper dictionaries to lists and sort by year
    for name, info in node_info.items():
        paper_list = list(info['paper_list'].values())
        for paper in paper_list:
            paper['reference'] = list(paper['reference'])
            paper['citation']  = list(paper['citation'])
        paper_list.sort(key=lambda x: -x['year'])

        info['paper_list'] = paper_list

    return node_info
