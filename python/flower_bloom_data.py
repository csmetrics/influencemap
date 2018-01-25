import pandas as pd
import networkx as nx
import numpy as np
from sklearn import preprocessing
from datetime import datetime

# Config setup
from config import *

# Turns the dataframe for flower into networkx graph
# Additionally normalises influence values
def score_df_to_graph(score_df):

    print('{} start graph generation\n---'.format(datetime.now()))

    # Ego Graph
    ego=score_df.ego
    egoG = nx.DiGraph(ego=ego, max_influenced=score_df['influenced'].max(), max_influencing=score_df['influencing'].max(), mapping=score_df.mapping, date_range=score_df.date_range)

    # Get top data for graph
    score_df = score_df[score_df.entity_id != ego].head(n=NUM_LEAVES)

    # Create a minimum and maximum processor object
    min_max_scaler = preprocessing.MinMaxScaler()

    num_leaves = min(NUM_LEAVES, len(min_max_scaler.fit_transform(score_df['influenced'].values.reshape(-1, 1))))
    normed_influenced = min_max_scaler.fit_transform(score_df['influenced'].values.reshape(-1, 1)).reshape(num_leaves)
    normed_influencing = min_max_scaler.fit_transform(score_df['influencing'].values.reshape(-1, 1)).reshape(num_leaves)
    normed_ratio = min_max_scaler.fit_transform(np.log(score_df['ratio']).values.reshape(-1, 1)).reshape(num_leaves)
    normed_sum = min_max_scaler.fit_transform(np.log(score_df['sum']).values.reshape(-1, 1)).reshape(num_leaves)

    # Add ego
    egoG.add_node(ego, weight=None)

    # Iterate over dataframe
    for i, (_, row) in enumerate(score_df.iterrows()):
        # Add ratio weight
        egoG.add_node(row['entity_id'], nratiow=normed_ratio[i], ratiow=row['ratio'], sumw=normed_sum[i], coauthor=row['coauthor'])

        # Add influence weights
        egoG.add_edge(row['entity_id'], ego, weight=row['influencing'], nweight=normed_influencing[i], direction='out')
        egoG.add_edge(ego, row['entity_id'], weight=row['influenced'], nweight=normed_influenced[i], direction='in')

    print('{} finish graph generation\n---'.format(datetime.now()))

    return egoG

if __name__ == "__main__":
    from mkAff import getAuthor
    from get_flower_df import gen_search_df
    from get_flower_data import generate_scores, generate_score_df, generate_coauthors
    from entity_type import *
    from draw_flower import draw_flower, draw_cite_volume
    import os, sys
    import sqlite3

    # out
    plot_dir = os.path.join(OUT_DIR, 'figures')

    # map
    e_map = Entity_map(Entity_type.AUTH, [Entity_type.AUTH])

    # input
    user_in = sys.argv[1]

    # get paper ids associated with input name
    _, id_2_paper_id, _ = getAuthor(user_in)

    conn = sqlite3.connect(DB_PATH)

    data_df = gen_search_df(conn, id_2_paper_id)

    influence_dict = generate_scores(conn, e_map, data_df, inc_self=False, unique=True)

    coauthors = generate_coauthors(e_map, data_df)

    for year in range(2000, 2018):
        score_df = generate_score_df(influence_dict, e_map, user_in, coauthors=coauthors, score_year_max=year)
        
        flower_graph = score_df_to_graph(score_df)

        draw_flower(egoG=flower_graph, filename=os.path.join(plot_dir, 'test_flower_{}.png'.format(year)))
        draw_cite_volume(egoG=flower_graph, filename=os.path.join(plot_dir, 'test_bar_{}.png'.format(year)))
