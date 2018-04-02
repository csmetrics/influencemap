import entity_type as ent
from flower_bloom_data import score_df_to_graph
from mag_interface import *
from mag_aggregate import *


"""
USER SEARHCES A name OF SOME e_type


FUNCTION 1
names, entity_list = name_to_entityq(name, e_type)
for entity in entity_list:
    disp to user
       -> Expands using get_id_papers (USER SELECTS PAPERS)

USER 1. RETURNS FILTER LIST
     2. ENTITY LIST
---
FUNCTION 2
influence_df = get_filtered_influence(entites, filters)
CACHE influence_df AS PERSISTENT IN USER SESSION FOR name

FUNCTION 3
fFILTER influence_df DEPENDENT ON influence_year AND self_cite
for leaf_var in leaves:
   score_entity(influence_df, each map def rom leaf_var)


"""


def get_auth_score_df(name):
    """
    """
    ego_name, paper_map = auth_name_to_paper_map(name)
    citation_score = paper_id_to_citation_score(paper_map, ent.Entity_type.AUTH)
    reference_score = paper_id_to_reference_score(paper_map, ent.Entity_type.AUTH)
    score_df = gen_score_df(citation_score, reference_score)
    score_df.ego = ego_name
    score_df.ego_type = ent.Entity_type.AUTH
    return score_df


def get_entity_score_df(name, e_type):
    if e_type == ent.Entity_type.AUTH:
        return get_auth_score_df(name)

    
def get_flower(score_df, leaves, bot_year=None, top_year=None):
    """
    """
    ego_name = score_df.ego
    flower_map = ent.Entity_map(score_df.ego_type, leaves)
    entity_score = score_entity(score_df, flower_map)
    agg_score = agg_score_df(entity_score, flower_map, score_df.ego, \
        score_year_min=bot_year, score_year_max=top_year)
    agg_score = agg_score[agg_score['entity_id'] != ego_name]
    agg_score.ego = ego_name
    print(agg_score)
    return score_df_to_graph(agg_score)


def get_flowers(score_df, cbfunc=lambda x, y: print("{}\t{}".format(x,y)), \
    bot_year=None, top_year=None):
    """
    """
    cbfunc(00, "drawing entity_to_auth flower")
    entity_to_auth = get_flower(score_df, [ent.Entity_type.AUTH], \
        bot_year=bot_year, top_year=top_year)
    cbfunc(30, "drawed entity_to_auth flower")

    cbfunc(30, "drawing entity_to_conf flower")
    entity_to_conf = get_flower(score_df, \
        [ent.Entity_type.CONF, ent.Entity_type.JOUR], \
        bot_year=bot_year, top_year=top_year)
    cbfunc(60, "drawed entity_to_conf flower")

    cbfunc(60, "drawing entity_to_affi flower")
    entity_to_affi = get_flower(score_df, [ent.Entity_type.AFFI], \
        bot_year=bot_year, top_year=top_year)
    cbfunc(90, "drawed entity_to_affi flower")

    cbfunc(100, "done")
    return entity_to_auth, entity_to_conf, entity_to_affi
