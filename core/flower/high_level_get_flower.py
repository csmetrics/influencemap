from webapp.utils import progressCallback, resetProgress
from webapp.graph import processdata
import core.utils.entity_type as ent
from core.flower.draw_flower_test import draw_flower
from core.flower.flower_bloomer import getFlower, getPreFlowerData
from core.search.mag_flower_bloom import *
from core.utils.get_entity import entity_from_name
from core.search.influence_df import get_filtered_score, get_unfiltered_score

flower_leaves = { 'author': [ent.Entity_type.AUTH]
                , 'conf': [ent.Entity_type.CONF, ent.Entity_type.JOUR]
                , 'inst': [ent.Entity_type.AFFI]
    }

str_to_ent = {
        "author": ent.Entity_type.AUTH,
        "conference": ent.Entity_type.CONF,
        "journal": ent.Entity_type.JOUR,
        "institution": ent.Entity_type.AFFI
    }

def get_flower_data_high_level(entitytype, authorids, normalizedname, selection=None):

    min_year = None
    max_year = None

    # USER NEEDS TO SELECT ENTITIES FIRST
    entity_list_init = list()
    filters = dict()
    for eid in authorids:
        entity = ent.Entity(normalizedname, eid, str_to_ent[entitytype])
        entity_list_init.append(entity)
        if selection != None:
            filters[entity] = list(map(lambda x : x['eid'], selection[eid]))

    print(entity_list_init)

    entity_list = list()
    for entity in entity_list_init:
        # Need to render and allow user selection here
        print(entity.entity_id, entity.get_papers())
        if entity.get_papers() is not None:
            entity_list.append(entity)

    # Get the entity names
    entity_names = list(map(lambda x: str.lower(x.entity_name), entity_list))
    entity_names.append('')
    print(entity_names)

    cache_score = [None, None, None]
    flower_score = [None, None, None]

    for i, flower_item in enumerate(flower_leaves.items()):
        name, leaves= flower_item

        if selection != None:
            entity_score_cache = get_filtered_score(entity_list, filters, leaves)
        else:
            entity_score_cache = get_unfiltered_score(entity_list, leaves)

        entity_score = entity_score_cache[~entity_score_cache['entity_id'].str.lower().isin(
                                          entity_names)]

        print(entity_score)
        agg_score = agg_score_df(entity_score, min_year, max_year)
        agg_score.ego = entity_names[0]
        print(agg_score)

        score = score_df_to_graph(agg_score)
        print(score)

        cache_score[i] = entity_score_cache
        flower_score[i] = score

    author_data = processdata("author", flower_score[0])
    conf_data = processdata("conf", flower_score[1])
    inst_data = processdata("inst", flower_score[2])

    return (author_data, conf_data, inst_data)


