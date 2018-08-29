'''
Flower functions for node information.
'''

import numpy as np
from datetime import datetime

def select_node_info(influence_df, node_names):
    '''
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
    for entity_info, node_influence in filtered_influence.groupby(node_cols):
        info = dict()
        entity_name, _ = entity_info

        # List of dictionaries per node entity for timeline
        node_info[entity_name] = list()       

        ego_group = node_influence.groupby(['ego_paper_id', 'publication_year'])
        for ego_paper_attr, ego_df in ego_group:
            # Ego attributes
            ego_paper_id, ego_paper_year = ego_paper_attr
            ego_paper_res = {'year': int(ego_paper_year)}

            # Get reference papers
            ref_df    = ego_df[ ego_df['is_ref'] ]
            ref_links = list(set(ref_df['link_paper_id'].astype('int').tolist()))

            # Get citation papers
            cit_df    = ego_df[ ego_df['is_cit'] ]
            cit_links = list(set(cit_df['link_paper_id'].astype('int').tolist()))

            ego_paper_res['ego_paper'] = int(ego_paper_id)
            ego_paper_res['reference'] = ref_links
            ego_paper_res['citation']  = cit_links

            node_info[entity_name].append(ego_paper_res)

        node_info[entity_name].sort(key=lambda x: -x['year'])

    return node_info
