# standard python imports
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
from get_flower_data import generate_scores, generate_score_df
from get_flower_df import gen_search_df
from entity_type import Entity, Entity_map
from draw_egonet import draw_halfcircle, draw_twoway_halfcircle
from influence_weight import get_weight
from flower_bloom_data import get_flower_df, flower_df_to_graph
from draw_flower import draw_flower, draw_cite_volume

# Config setup
from config import *

weight_types = [ 'citing authors', 'cited authors', 'citing references']
wfunc_test = lambda sdict : (lambda x, y : get_weight(x, y, tweight=sdict))

def flower_wtest(conn, data_df, scheme, name, n):
    sdict = dict()
    for i, val in enumerate(scheme):
        if val:
            sdict[weight_types[i]] = True
        else:
            sdict[weight_types[i]] = False

    influence_dict = generate_scores(conn, Entity_map(Entity.AUTH, Entity.AUTH), data_df, inc_self=False, calc_weight=wfunc_test(sdict))

    score_df = generate_score_df(influence_dict)
    
    flower_df = get_flower_df(score_df, user_in)

    flower_graph = flower_df_to_graph(flower_df, user_in)

    plot_dir = os.path.join(OUT_DIR, 'figures')

    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)

    draw_flower(egoG=flower_graph, filename=os.path.join(plot_dir, 'weight_combination_flower{}.png'.format(n)))
    draw_cite_volume(egoG=flower_graph, filename=os.path.join(plot_dir, 'weight_combination_bar{}.png'.format(n)))

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
