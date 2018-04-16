import pandas as pd
from mag_interface import *


def score_entity(score_df, entity_map):
    """
    """
    ego, leaves = entity_map.get_map()
    paper_ids = list(set(score_df['paper_id']))
    data_dict = list()

    for e_type in leaves:
        entity_query = {
            "path": "/paper/{}/entity".format(e_type.api_id),
            "paper": {
                 "type": "Paper",
                 "id": paper_ids,
                 "select": [ e_type.api_id ]
                 },
            "entity": {
                 "select": [ e_type.api_name ]
                 }
            }

        data = query_academic_search('post', JSON_URL, entity_query)
        for paper, entity in data['Results']:
            row = dict()
            row['paper_id'] = paper['CellID']
            row['entity_id'] = entity[e_type.api_name]
            data_dict.append(row)

    entity_df = pd.DataFrame(data_dict)
    weight_influenced = entity_df['paper_id'].value_counts().to_frame('weight').reset_index()

    # Weight scores
    ego_paper_ids = list(set(score_df['info_from']))

    ego_query = {
            "path": "/paper/{}/entity".format(ego.api_id),
            "paper": {
                "type": "Paper",
                "id": ego_paper_ids,
                "select": [ ego.api_id ]
                },
            "entity": {
                "select": [ ego.api_name ]
                }
            }

    info_from_data = query_academic_search('post', JSON_URL, ego_query)
    ego_dict = list()
    for paper, entity in info_from_data['Results']:
        row = dict()
        row['paper_id'] = paper['CellID']
        row['entity_id'] = entity[ego.api_name]
        ego_dict.append(row)

    ego_df = pd.DataFrame(ego_dict)
    weight_influencing = ego_df['paper_id'].value_counts().to_frame('weight').reset_index()

    rename_dict_influenced = {'index': 'paper_id'}
    rename_dict_influencing = {'index': 'info_from'}
    weight_influenced.rename(columns=rename_dict_influenced, inplace=True)
    weight_influencing.rename(columns=rename_dict_influencing, inplace=True)

    score_df = pd.merge(score_df, weight_influenced, how='outer',
                        on='paper_id', sort=False)
    score_df['influenced'] = score_df['influenced'] / score_df['weight']
    score_df.drop('weight', axis=1, inplace=True)

    score_df = pd.merge(score_df, weight_influencing, how='outer',
                        on='info_from', sort=False)
    score_df['influencing'] = score_df['influencing'] / score_df['weight']
    score_df.drop('weight', axis=1, inplace=True)

    entity_score_df = pd.merge(entity_df, score_df, on='paper_id', sort=False)

    return entity_score_df
