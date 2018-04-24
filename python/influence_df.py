import os
import pandas as pd
from config import *
from mag_interface import *

def entity_to_citation_score(entity):
    """
        Turns an author ids into a list of papers associated to the ids.
    """
    entity_id = entity.entity_id
    e_type = entity.entity_type
    paper_ids = entity.get_papers()['paper_id'].tolist()

    query = {
        "path": "/paper/CitationIDs/cites",
        "paper": {
            "type": "Paper",
            "id": paper_ids,
            "select": [
                "PublishDate",
                e_type.api_id
                ]
            },
        "cites": {
            "select": [
                "PublishDate",
                e_type.api_id
                ]
            }
        }

    data = query_academic_search('post', JSON_URL, query)
    data_sc = list()
    for ego, cite in data['Results']:
        row = dict()
        row['info_from'] = ego['CellID']
        #row['paper_other'] = cite['CellID']
        row['paper_id'] = cite['CellID']
        row['influenced'] = 1 #/ len(ego['AuthorIDs'])
        row['influencing'] = 0
        row['self_cite'] = 0 if entity_id in cite['AuthorIDs'] else 1
        #row['date_ego'] = ego['PublishDate']
        row['influence_date'] = to_datetime(cite['PublishDate'])
        data_sc.append(row)

    cite_df = pd.DataFrame(data_sc)
    cite_df['e_type'] = e_type

    return cite_df


def entity_to_reference_score(entity):
    """
        Turns an author ids into a list of papers associated to the ids.
    """
    entity_id = entity.entity_id
    e_type = entity.entity_type
    paper_ids = entity.get_papers()['paper_id'].tolist()

    query = {
        "path": "/paper/ReferenceIDs/refs",
        "paper": {
            "type": "Paper",
            "id": paper_ids,
            "select": [
                "PublishDate",
                e_type.api_id
                ]
            },
        "refs": {
            "select": [
                "PublishDate",
                e_type.api_id
                ]
            }
        }

    data = query_academic_search('post', JSON_URL, query)
    data_sc = list()
    for ego, refs in data['Results']:
        row = dict()
        row['info_from'] = ego['CellID']
        #row['paper_other'] = refs['CellID']
        row['paper_id'] = refs['CellID']
        row['influenced'] = 0
        row['influencing'] = 1 #/ len(refs['AuthorIDs'])
        row['self_cite'] = 0 if entity_id in refs['AuthorIDs'] else 1
        row['influence_date'] = to_datetime(ego['PublishDate'])
        #row['influence_year'] = cite['PublishDate']
        data_sc.append(row)

    ref_df = pd.DataFrame(data_sc)
    ref_df['e_type'] = e_type

    return ref_df


def get_influence_df(entity):
    """
    """
    cache_path = os.path.join(CACHE_INFLUENCE_DIR, entity.cache_str())

    try:
        influence_df = pd.read_pickle(cache_path)

    except FileNotFoundError:
        cites = entity_to_citation_score(entity)
        refs = entity_to_reference_score(entity)

        influence_df = pd.concat([cites, refs])

        influence_df.to_pickle(cache_path)
        os.chmod(cache_path, 0o777)

    return influence_df


def get_filtered_influence(entity_list, filters):
    """
    """
    influence_list = list()
    influence_dict = dict()
    for entity in entity_list:
        info_df = get_influence_df(entity)

        try:
            ignores = filters[entity.entity_id]
            info_df = info_df[~info_df['info_from'].isin(ignores)]
        except KeyError:
            pass

        influence_list.append(info_df)

    return pd.concat(influence_list)
