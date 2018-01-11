import pandas as pd
import networkx as nx
import numpy as np
from sklearn import preprocessing

# Config setup
from config import *

# Generates a sublist of the score_df for making a flower and sort with respect
# the ratio
def get_flower_df(score_df, ego):
    return score_df[score_df.entity_id != ego].head(n=NUM_LEAVES) #.sort_values('ratio', ascending=False)

# Turns the dataframe for flower into networkx graph
# Additionally normalises influence values
def flower_df_to_graph(score_df, ego):
    # Create a minimum and maximum processor object
    min_max_scaler = preprocessing.MinMaxScaler()

    normed_influenced = min_max_scaler.fit_transform(score_df['influenced'].values.reshape(-1, 1)).reshape(NUM_LEAVES)
    normed_influencing = min_max_scaler.fit_transform(score_df['influencing'].values.reshape(-1, 1)).reshape(NUM_LEAVES)
    normed_ratio = min_max_scaler.fit_transform(np.log(score_df['ratio']).values.reshape(-1, 1)).reshape(NUM_LEAVES)
    normed_sum = min_max_scaler.fit_transform(np.log(score_df['sum']).values.reshape(-1, 1)).reshape(NUM_LEAVES)

    # Ego Graph
    egoG = nx.DiGraph(ego=ego, max_influenced=score_df['influenced'].max(), max_influencing=score_df['influencing'].max())

    # Add ego
    egoG.add_node(ego, weight=None)

    # Iterate over dataframe
    for i, (_, row) in enumerate(score_df.iterrows()):
        # Add ratio weight
        egoG.add_node(row['entity_id'], nratiow=normed_ratio[i], ratiow=row['ratio'], sumw=normed_sum[i])

        # Add influence weights
        egoG.add_edge(ego, row['entity_id'], weight=row['influencing'], nweight=normed_influencing[i], direction='out')
        egoG.add_edge(row['entity_id'], ego, weight=row['influenced'], nweight=normed_influenced[i], direction='in')

    return egoG

if __name__ == "__main__":
    from mkAff import getAuthor
    from get_flower_df import gen_search_df
    from get_flower_data import generate_scores, generate_score_df
    from entity_type import *
    from draw_flower import draw_flower, draw_cite_volume
    import os, sys
    import sqlite3

    # input
    user_in = sys.argv[1]

    # get paper ids associated with input name
    _, id_2_paper_id = getAuthor(user_in)

    conn = sqlite3.connect(DB_PATH)

    data_df = gen_search_df(conn, id_2_paper_id)

    influence_dict = generate_scores(conn, Entity_map(Entity.AUTH, Entity.AUTH), data_df, inc_self=True)
    score_df = generate_score_df(influence_dict)
    
    flower_df = get_flower_df(score_df, user_in)

    flower_graph = flower_df_to_graph(flower_df, user_in)

    plot_dir = os.path.join(OUT_DIR, 'figures')

    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)

    draw_flower(egoG=flower_graph, filename=os.path.join(plot_dir, 'test_flower.png'))
    draw_cite_volume(egoG=flower_graph, filename=os.path.join(plot_dir, 'test_bar.png'))
