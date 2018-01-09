# standard python imports
import json
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
from get_flower_data import *
from get_flower_df import gen_search_df
from entity_type import Entity, Entity_map
from draw_egonet import draw_halfcircle

# Config setup
with open('config.json') as config_data:
    config = json.load(config_data)
    DB_DIR = config['sqlite3']['directory']
    DB_PATH = os.path.join(DB_DIR, config['sqlite3']['name'])
    OUT_DIR = config['data']['out']
    NUM_LEAVES = config['flower']['leaves']

def getEntityMap(ego, outer):
    e = {'author': Entity.AUTH, 'conference': Entity.CONF, 'institution': Entity.AFFI, 'journal': Entity.JOURN}
    return Entity_map(e[ego], e[outer])

def drawFlower(conn, ent_type, ent_type2, data_df, dir_out, name):   
    # Generate associated author scores for citing and cited
    influence_dict = generate_scores(conn, Entity_map(ent_type, ent_type2), data_df)
    citing_records = influence_dict['influenced']
    cited_records = influence_dict['influencing']

    #### START PRODUCING GRAPH
    plot_dir = os.path.join(dir_out, 'figures')

    for dir in [dir_out, plot_dir]:
      if not os.path.exists(dir):
          os.makedirs(dir)

    # get the top x influencersdrawFlower(conn, Entity.AUTH, citing_papers, cited_papers, my_ids, filter_dict, dir_out)
    top_entities_influenced_by_poi = [(k, citing_records[k]) for k in sorted(citing_records, key=citing_records.get, reverse = True)][:NUM_LEAVES]
    top_entities_that_influenced_poi = [(k, cited_records[k]) for k in sorted(cited_records, key=cited_records.get, reverse = True)][:NUM_LEAVES]
    

    # build a graph structure for the top data
    personG = nx.DiGraph()

    for entity in top_entities_that_influenced_poi:
      # note that edge direction is with respect to influence, not citation i.e. for add_edge(a,b,c) it means a influenced b with a weight of c 
      personG.add_edge(entity[0], name, weight=float(entity[1]))

    for entity in top_entities_influenced_by_poi:
      personG.add_edge(name, entity[0], weight=float(entity[1]))

    influencedby_filename = os.path.join(plot_dir, 'influencedby_{}.png'.format(ent_type2))
    influencedto_filename = os.path.join(plot_dir, 'influencedto_{}.png'.format(ent_type2))
    print("drawing graphs")
    draw_halfcircle(graph=personG, ego=name, renorm_weights='log', direction='in', filename = influencedby_filename)
    draw_halfcircle(graph=personG, ego=name, renorm_weights='log', direction='out', filename = influencedto_filename)
    print("finished graphs")
    return influencedby_filename, influencedto_filename


def getFlower(id_2_paper_id, name, ent_type):
    conn = sqlite3.connect(DB_PATH)

    # get paper ids associated with input name
    print("\n\nid_to_paper_id\n\n\n\n\n\n{}".format(id_2_paper_id))

    # filter ref papers
    data_df = gen_search_df(conn, id_2_paper_id)

    # Generate a self filter dictionary
    entity_to_author = drawFlower(conn, ent_type,  "author" , data_df, OUT_DIR, name)
    entity_to_conference = drawFlower(conn, ent_type, "conf", data_df, OUT_DIR, name)
    entity_to_affiliation = drawFlower(conn, ent_type, "institution" , data_df, OUT_DIR, name)

    conn.close()
    file_names = []
    for ls in [entity_to_author, entity_to_conference, entity_to_affiliation]:
        file_names.extend(ls)
    return file_names
