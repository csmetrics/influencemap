# standard python imports
import json
import sqlite3
import os, sys
from datetime import datetime
import pandas as pd
import networkx as nx
import seaborn as sns
import matplotlib.pyplot as plt
sns.set()
plt.switch_backend('agg')

# local module imports
from mkAff import getAuthor
from get_flower_data import generate_scores
from get_flower_df import gen_search_df
from entity_type import Entity, Entity_map
from draw_egonet import draw_halfcircle
from influence_weight import get_weight

weight_types = [ 'citing authors', 'cited authors', 'citing references']
wfunc_test = lambda sdict : (lambda x, y : get_weight(x, y, tweight=sdict))

# Config setup
with open('config.json') as config_data:
    config = json.load(config_data)
    DB_DIR = config['sqlite3']['directory']
    DB_PATH = os.path.join(DB_DIR, config['sqlite3']['name'])
    OUT_DIR = config['data']['out']
    NUM_LEAVES = config['flower']['leaves']

def flower_wtest(conn, data_df, scheme, name, n):
    sdict = dict()
    for i, val in enumerate(scheme):
        if val:
            sdict[weight_types[i]] = True
        else:
            sdict[weight_types[i]] = False

    influence_dict = generate_scores(conn, Entity_map(Entity.AUTH, Entity.AUTH), data_df, inc_self=True, calc_weight=wfunc_test(sdict))
    citing_records = influence_dict['influenced']
    cited_records = influence_dict['influencing']
    
    #### START PRODUCING GRAPH
    plot_dir = os.path.join(OUT_DIR, 'figures')

    for dir in [OUT_DIR, plot_dir]:
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

    influencedby_filename = os.path.join(plot_dir, 'influencedby_{}.png'.format(n))
    influencedto_filename = os.path.join(plot_dir, 'influencedto_{}.png'.format(n))
    print("drawing graphs")
    draw_halfcircle(graph=personG, ego=name, renorm_weights='log', direction='in', filename = influencedby_filename)
    draw_halfcircle(graph=personG, ego=name, renorm_weights='log', direction='out', filename = influencedto_filename)
    print("finished graphs")
    

if __name__ == '__main__':
    import itertools

    # input
    user_in = sys.argv[1]

    # get paper ids associated with input name
    _, id_2_paper_id = getAuthor(user_in)

    conn = sqlite3.connect(DB_PATH)

    # Data dataframe
    data_df = gen_search_df(conn, id_2_paper_id)

    schemes = list()
    for i, scheme in enumerate(itertools.product([True, False], repeat=3)):
        print('{} start creating flower {} with scheme: [{}]'.format(datetime.now(), i, ', '.join(map(str, scheme))))
        flower_wtest(conn, data_df, scheme, user_in, i)
        print('{} finish creating flower {} with scheme: [{}]'.format(datetime.now(), i, ', '.join(map(str, scheme))))
        schemes.append((i,scheme))

    print('[{}]'.format(', '.join(map(str, weight_types))))
    for i, scheme in schemes:
        print('{}: [{}]'.format(i, ', '.join(map(str, scheme))))
