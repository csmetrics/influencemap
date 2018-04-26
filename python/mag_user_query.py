import entity_type as ent
import pandas as pd
from mag_interface import *


def paperq_to_dict(paper_query):
    paper_row_dict = {
            'paper_id': paper_query['CellID'],
            'paper_name': paper_query['NormalizedTitle'],
            'cite_count': paper_query['CitationCount'],
            'pub_date': to_datetime(paper_query['PublishDate'])
        }

    return paper_row_dict

def get_ent_paper_df_gen(entity):
    """
    """
    entity_id = entity.entity_id
    e_type = entity.entity_type
    query = {
        "path": "/entity/PaperIDs/papers",
        "entity": {
            "type": e_type.api_type,
            "id": [ entity_id ],
            },
        "papers": {
                "select": ["NormalizedTitle", "CitationCount", "PublishDate"]
            }
        }

    print("Test")
    print(query)
    data = query_academic_search('post', JSON_URL, query)
    paper_res = data['Results']
    print(paper_res)

    if not paper_res:
        return None

    paper_list = list()
    for res_row in paper_res:
        paper = res_row[1]
        paper_list.append(paperq_to_dict(paper))

    entity.paper_df = pd.DataFrame(paper_list)

    return entity.paper_df

def get_ent_paper_df_conf(entity):
    """
    """
    entity_id = entity.entity_id
    e_type = entity.entity_type
    query = {
        "path": "/paper",
        "paper": {
            "type": "Paper",
            "match": {
                "NormalizedVenue": entity_id
                },
            "select": [ "OriginalVenue", "NormalizedTitle", "CitationCount",
                        "PublishDate" ]
            }
        }

    data = query_academic_search('post', JSON_URL, query)
    paper_res = data['Results']

    if not paper_res:
        return None

    paper_list = list()
    for res_row in paper_res:
        paper = res_row[0]
        paper_list.append(paperq_to_dict(paper))

    entity.paper_df = pd.DataFrame(paper_list)

    return entity.paper_df

def ent_paper_df(entity):
    """
    """
    print("Generating scores for:", entity.entity_id)
    if entity.entity_type == ent.Entity_type.CONF:
        entity_update = get_ent_paper_df_conf(entity)
    else:
        entity_update = get_ent_paper_df_gen(entity)
    print("Finishing generating scores for:", entity.entity_id)

    return entity_update
