import entity_type as ent
import pandas as pd
from mag_interface import *


def name_to_entityq(name, e_type):
    """
    """
    name_tag = e_type.api_name
    query = {
       "path": "/entity",
       "entity": {
           "type": e_type.api_type,
           "match": {
               "Name": name
               },
           "select": [ name_tag ]
           }
       }

    data = query_academic_search('post', JSON_URL, query)

    entity_list = list()
    name_dict = dict()

    for entity in data['Results']:
        entity = ent.Entity(entity[0]['CellID'], e_type)
        entity_list.append(entity)
        try:
            name_dict[entity[0][name_tag]] += 1
        except KeyError:
            name_dict[entity[0][name_tag]] = 1

    n_tmp = sorted(name_dict.items(), key=operator.itemgetter(1), reverse=True)
    names = [name_tuple[0] for name_tuple in n_tmp]

    return names, entity_list


def get_id_papers(entity):
    """
    """
    cache_path = os.path.join(CACHE_DIR, entity.cache_str())
    try:
        id_df = pd.read_pickle(cache_path)
    except FileNotFoundError:
        id_df = entity.get_entity_papers()
    
        # Cache 
        id_df.to_pickle(cache_path)
        os.chmod(cache_path, 0o777)

    return id_df


def entity_name_to_paper_map(name, e_type):
    """
    """
    has_paper_id = [ent.Entity_type.AUTH.api_type,
                    ent.Entity_type.AFFI.api_type]

    if e_type.api_type not in has_paper_id:
        raise ValueError('API field not implemented for type')

    name_tag = e_type.api_name
    query = {
        "path": "/entity/PaperIDs/paper",
        "entity": {
            "type": e_type.api_type,
            "match": {
                "Name": name
                },
            "select": [ name_tag, "PaperIDs" ]
            }
        }

    data = query_academic_search('post', JSON_URL, query)
    paper_map = dict()
    name_dict = dict()
    for entity in data['Results']:
        paper_map[entity[0]['CellID']] = entity[0]['PaperIDs']
        try:
            name_dict[entity[0][name_tag]] += 1
        except KeyError:
            name_dict[entity[0][name_tag]] = 1
    
    n_tmp = sorted(name_dict.items(), key=operator.itemgetter(1), reverse=True)
    names = [name_tuple[0] for name_tuple in n_tmp]
    return names, paper_map


#def get_paper_user_info
