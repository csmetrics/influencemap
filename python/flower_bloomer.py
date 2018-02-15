# standard python imports
import sqlite3
import os, sys
from datetime import datetime
import pandas as pd
import numpy as np
import networkx as nx
import seaborn as sns
import matplotlib.pyplot as plt
sns.set()
plt.switch_backend('agg')

# local module imports
from get_flower_data import generate_scores, generate_score_df, generate_coauthors
from get_flower_df import gen_search_df
from entity_type import * #Entity, Entity_map, Entity_type
from draw_flower import draw_flower
from flower_bloom_data import score_df_to_graph

# Config setup
from config import *

e = {'author': Entity_type.AUTH, 'conference': Entity_type.CONF, 'institution': Entity_type.AFFI, 'journal': Entity_type.JOUR}

def getEntityMap(ego, outer):
    return Entity_map(e[ego], [e[outer]])

def drawFlower(conn, ent_type, ent_type2, data_df, dir_out, name, bot_year=None, top_year=None, inc_self=False):
    # Generate associated author scores for citing and cited
    e_map = getEntityMap(ent_type, ent_type2)

    influence_dict = generate_scores(conn, e_map, data_df, inc_self=inc_self)

    coauthors = generate_coauthors(e_map, data_df)

    score_df = generate_score_df(influence_dict, e_map, name, coauthors=coauthors, score_year_min=bot_year, score_year_max=top_year)

    flower_graph = score_df_to_graph(score_df)
    
    #### START PRODUCING GRAPH
    plot_dir = os.path.join(dir_out, 'figures')

    for dir in [dir_out, plot_dir]:
      if not os.path.exists(dir):
          os.makedirs(dir)

    name_for_filename = "_".join(name.split())
    
    image_filename = '{}_flower_{}.png'.format(name_for_filename, ent_type2)

    image_path = os.path.join(plot_dir, image_filename)

    return flower_graph

def getPreFlowerData(id_2_paper_id, unselected_id_2_paper_id, ent_type, cbfunc=lambda x, y: print("{}\t{}".format(x,y))): # id_2_paper_id should be a dict eid: [pid] including all papers regardless if they were deselected
    conn = sqlite3.connect(DB_PATH)

    # get paper ids associated with input name
    cbfunc(10, "get paper ids associated with input name")

    entity_map = dict()

    entity_id_2_paper_id = dict()
    for eid, papers in id_2_paper_id.items():
        entity = Entity(eid, e[ent_type])
        entity_map[eid] = entity
        entity_id_2_paper_id[entity] = papers

    # Initiate the unselect dictionary
    entity_unselected_id_2_paper_id = dict([(entity, []) for entity in entity_map.values()])

    # Set unselect values
    for eid, papers in unselected_id_2_paper_id.items():
        entity_unselected_id_2_paper_id[entity_map[eid]] = papers

    # filter ref papers
    cbfunc(20, "filter reference papers")
    data_df = gen_search_df(conn, entity_id_2_paper_id, entity_unselected_id_2_paper_id)

    conn.close()

    cbfunc(30, "generating flower data")
    return data_df

def getFlower(data_df, name, ent_type, cbfunc=lambda x, y: print("{}\t{}".format(x,y)), bot_year=None, top_year=None, inc_self=False):
    conn = sqlite3.connect(DB_PATH)

    # Generate a self filter dictionary
    cbfunc(40, "draw entity_to_author flower")
    entity_to_author = drawFlower(conn, ent_type, "author", data_df, OUT_DIR, name, bot_year=bot_year, top_year=top_year, inc_self=inc_self)

    cbfunc(60, "draw entity_to_conference flower")
    entity_to_conference = drawFlower(conn, ent_type, "conference", data_df, OUT_DIR, name, bot_year=bot_year, top_year=top_year, inc_self=inc_self)

    cbfunc(80, "draw entity_to_affiliation flower")
    entity_to_affiliation = drawFlower(conn, ent_type, "institution", data_df, OUT_DIR, name, bot_year=bot_year, top_year=top_year, inc_self=inc_self)
 
    conn.close()

    cbfunc(100, "done")
    file_names = [entity_to_author, entity_to_conference, entity_to_affiliation]
    return file_names
