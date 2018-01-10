import pandas as pd
import networkx as nx

# Config setup
from config import *

# Generates a sublist of the score_df for making a flower and sort with respect
# the ratio
def get_flower_df(score_df):
    return score_df.head(n=NUM_LEAVES).sort_values('ratio', ascending=False)

def flower_df_to_graph(score_df, ego):
    egoG = nx.DiGraph()

    # Add ego
    egoG.add_node(ego)

    # Iterate over dataframe
    for i, row in score_df.iterrows():
        # Add ratio weight
        egoG.add_node(row['entity id'], weight=row['ratio'])

        # Add influence weights
        egoG.add_edge(ego, row['entity id'], weight=row['influenced'])
        egoG.add_edge(row['entity id'], ego, weight=row['influencing'])

    return egoG

if __name__ == "__main__":
    from mkAff import getAuthor
    from get_flower_df import gen_search_df
    from get_flower_data import generate_scores, generate_score_df
    from entity_type import *
    import os, sys
    import sqlite3

    # input
    user_in = sys.argv[1]

    # get paper ids associated with input name
    _, id_2_paper_id = getAuthor(user_in)

    conn = sqlite3.connect(DB_PATH)

    data_df = gen_search_df(conn, id_2_paper_id)

    influence_dict = generate_scores(conn, Entity_map(Entity.AUTH, Entity.CONF), data_df, inc_self=True)
    score_df = generate_score_df(influence_dict)
    
    flower_df = get_flower_df(score_df)

    print(flower_df_to_graph(flower_df, user_in))
