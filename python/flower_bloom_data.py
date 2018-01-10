import pandas as pd
import networkx as nx
import numpy as np

# Config setup
from config import *

# Generates a sublist of the score_df for making a flower and sort with respect
# the ratio
def get_flower_df(score_df):
    return score_df.head(n=NUM_LEAVES) #.sort_values('ratio', ascending=False)

# Turns the dataframe for flower into networkx graph
# Additionally normalises influence values
def flower_df_to_graph(score_df, ego):

    # Normalise dataframe values 
    influenced_max = score_df['influenced'].max()
    influencing_max = score_df['influencing'].max()

    score_df['normed influenced'] = np.vectorize(lambda x : x / influenced_max)(score_df['influenced'])
    score_df['normed influencing'] = np.vectorize(lambda x : x / influencing_max)(score_df['influencing'])

    # Ego Graph
    egoG = nx.DiGraph(ego=ego)

    # Add ego
    egoG.add_node(ego, weight=None)

    # Iterate over dataframe
    for i, row in score_df.iterrows():
        # Add ratio weight
        egoG.add_node(row['entity id'], weight=row['ratio'])

        # Add influence weights
        egoG.add_edge(ego, row['entity id'], weight=row['normed influencing'], direction='out')
        egoG.add_edge(row['entity id'], ego, weight=row['normed influenced'], direction='in')

    return egoG

if __name__ == "__main__":
    from mkAff import getAuthor
    from get_flower_df import gen_search_df
    from get_flower_data import generate_scores, generate_score_df
    from entity_type import *
    from draw_flower import draw_flower
    import os, sys
    import sqlite3

    # input
    user_in = sys.argv[1]

    # get paper ids associated with input name
    _, id_2_paper_id = getAuthor(user_in, lambda _ : None)

    conn = sqlite3.connect(DB_PATH)

    data_df = gen_search_df(conn, id_2_paper_id)

    influence_dict = generate_scores(conn, Entity_map(Entity.AUTH, Entity.CONF), data_df, inc_self=True)
    score_df = generate_score_df(influence_dict)
    
    flower_df = get_flower_df(score_df)

    flower_graph = flower_df_to_graph(flower_df, user_in)


    plot_dir = os.path.join(OUT_DIR, 'figures')

    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)

    draw_flower(egoG=flower_graph, filename=os.path.join(plot_dir, 'test.png'))
