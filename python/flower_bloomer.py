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
from get_flower_data_memory import *
from export_citations_author import construct_cite_db
from entity_type import Entity, Entity_map
from draw_egonet import draw_halfcircle

def getEntityMap(ego, outer):
    e = {'author': Entity.AUTH, 'conf': Entity.CONF, 'institution': Entity.AFFI}
    return Entity_map(e[ego], e[outer])

def drawFlower(conn, ent_type, ent_type2, citing_papers, cited_papers, filter_dict, dir_out, name):   
    # Generate associated author scores for citing and cited
    citing_records = gen_score(conn, getEntityMap(ent_type,ent_type2), citing_papers, fdict=filter_dict)
    cited_records = gen_score(conn, getEntityMap(ent_type, ent_type2), cited_papers, fdict=filter_dict)


    #### START PRODUCING GRAPH
    plot_dir = os.path.join(dir_out, 'figures')

    for dir in [dir_out, plot_dir]:
      if not os.path.exists(dir):
          os.makedirs(dir)

    # get the top x influencersdrawFlower(conn, Entity.AUTH, citing_papers, cited_papers, my_ids, filter_dict, dir_out)
    n = 25
    top_entities_influenced_by_poi = [(k, citing_records[k]) for k in sorted(citing_records, key=citing_records.get, reverse = True)][:n]
    top_entities_that_influenced_poi = [(k, cited_records[k]) for k in sorted(cited_records, key=cited_records.get, reverse = True)][:n]
    

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
    # db_dir = '/localdata/u5/influencemap'
    db_dir = "/localdata/u5642715/influenceMapOut"
    #db_name = 'paper.db'
    #db_path = os.path.join(db_dir, db_name)
    dir_out = '/localdata/u5798145/influencemap/out'

    db_path = os.path.join(db_dir, 'paper_info2.db')
    conn = sqlite3.connect(db_path)

    # get paper ids associated with input name
    print("\n\nid_to_paper_id\n\n\n\n\n\n{}".format(id_2_paper_id))

    #if ent_type == "conf":
    #    associated_papers = 
    associated_papers = get_papers(id_2_paper_id)
    print("\n\nassociated papers\n\n\n\n\n\n{}".format(associated_papers))
    # filter ref papers
    print('{} start filter paper references'.format(datetime.now()))
    citing_papers, cited_papers = construct_cite_db(conn, associated_papers)
    print('{} finish filter paper references'.format(datetime.now()))

    # Generate a self filter dictionary
    filter_dict = self_dict(id_2_paper_id)

    entity_to_author = drawFlower(conn, ent_type,  "author" , citing_papers, cited_papers, filter_dict, dir_out, name)
    entity_to_conference = drawFlower(conn, ent_type, "conf", citing_papers, cited_papers, filter_dict, dir_out, name)
    entity_to_affiliation = drawFlower(conn, ent_type, "institution" , citing_papers, cited_papers, filter_dict, dir_out, name)
    conn.close()
    file_names = []
    for ls in [entity_to_author, entity_to_conference, entity_to_affiliation]:
        file_names.extend(ls)
    return file_names

