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

    for entity in data['Results']:
        entityq = ent.Entity(entity[0][name_tag], entity[0]['CellID'], e_type)
        # Filter entities with no papers attached to them
        if entityq.get_papers().empty:
            continue

        # Otherwise append to entity list
        entity_list.append(entityq)

    return entity_list


#def get_id_papers(entity):
#    """
#    """
#    cache_path = os.path.join(CACHE_PAPERS_DIR, entity.cache_str())
#    try:
#        id_df = pd.read_pickle(cache_path)
#    except FileNotFoundError:
#        id_df = entity.get_entity_papers()
#    
#        # Cache 
#        id_df.to_pickle(cache_path)
#        os.chmod(cache_path, 0o777)
#
#    return id_df


#def get_paper_user_info
