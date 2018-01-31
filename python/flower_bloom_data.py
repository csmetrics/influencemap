import pandas as pd
import networkx as nx
import numpy as np
from datetime import datetime

# Config setup
from config import *

# Function to normalise data for a singular series
def normalise_singular_linear(series):
    max_val = series.max()
    min_val = series.min()

    max_min_dif = max_val - min_val

    # Cases if max equal to min
    if max_min_dif == 0 and max_val == 0:
        return series
    elif max_min_dif == 0:
        series = 1
        return series

    # Normalise
    return series.apply(lambda x : (x - min_val) / max_min_dif)

    # Scale from 1 to 1024
    scaled = series.apply(lambda x : 1 + (x - min_val) / max_min_dif)

    # Log down to 0 to 1
    return scaled.apply(np.log2)

# Normalise two series logwise
def normalise_double_log(series1, series2):
    max_val = max(series1.max(), series2.max())
    min_val = min(series1.min(), series2.min())

    max_min_dif = max_val - min_val

    # Cases if max equal to min
    if max_min_dif == 0 and max_val == 0:
        return series1, series2
    elif max_min_dif == 0:
        return pd.Series([1] * series.size), pd.Series([1] * series.size)

    # Scale from 1 to 1024
    scaled1 = series1.apply(lambda x : 1 + (x - min_val) / max_min_dif)
    scaled2 = series2.apply(lambda x : 1 + (x - min_val) / max_min_dif)

    # Log down to 0 to 1
    return scaled1.apply(np.log2), scaled2.apply(np.log2)

# Turns the dataframe for flower into networkx graph
# Additionally normalises influence values
def score_df_to_graph(score_df):

    print('{} start graph generation\n---'.format(datetime.now()))

    # Ego Graph
    ego=score_df.ego
    egoG = nx.DiGraph(ego=ego, max_influenced=score_df['influenced'].max(), max_influencing=score_df['influencing'].max(), mapping=score_df.mapping, date_range=score_df.date_range)

    # Get top data for graph
    score_df = score_df[score_df.entity_id != ego].head(n=NUM_LEAVES)

    # Normalise values
    score_df['normed_sum'] = normalise_singular_linear(score_df['sum'])
    score_df['normed_ratio'] = normalise_singular_linear(score_df['ratio'])
    norm_influenced, norm_influencing = normalise_double_log(score_df['influenced'], score_df['influencing'])
    score_df['normed_influenced'] = norm_influenced
    score_df['normed_influencing'] = norm_influencing

    # Add ego
    egoG.add_node(ego, weight=None)

    # Iterate over dataframe
    for _, row in score_df.iterrows():
        # Add ratio weight
        egoG.add_node(row['entity_id'], nratiow=row['normed_ratio'], ratiow=row['ratio'], sumw=row['normed_sum'], coauthor=row['coauthor'])

        # Add influence weights
        egoG.add_edge(row['entity_id'], ego, weight=row['influencing'], nweight=row['normed_influencing'], direction='out')
        egoG.add_edge(ego, row['entity_id'], weight=row['influenced'], nweight=row['normed_influenced'], direction='in')

    print('{} finish graph generation\n---'.format(datetime.now()))

    return egoG

if __name__ == "__main__":
    from mkAff import getAuthor
    from get_flower_df import gen_search_df
    from get_flower_data import generate_scores, generate_score_df, generate_coauthors
    from entity_type import *
    from draw_flower import draw_flower, draw_cite_volume
    from flower_helpers import *
    import os, sys
    import sqlite3
    import imageio

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

    influence_dict = generate_scores(conn, e_map, data_df, inc_self=False, unique=False)

    coauthors = generate_coauthors(e_map, data_df)

    score_df = generate_score_df(influence_dict, e_map, user_in, coauthors=coauthors)

    #flower_graph = score_df_to_graph(score_df)

    #draw_flower(egoG=flower_graph, filename=os.path.join(plot_dir, 'test_flower.png'))
    #draw_cite_volume(egoG=flower_graph, filename=os.path.join(plot_dir, 'test_bar.png'))

    images = list()

    for year in range(influence_df_min_year(influence_dict), 2018):
        score_df = generate_score_df(influence_dict, e_map, user_in, coauthors=coauthors, score_year_max=year)
        
        flower_graph = score_df_to_graph(score_df)

        path_name = os.path.join(plot_dir, '{}_flower_{}.png'.format(user_in, year))
        draw_flower(egoG=flower_graph, filename=path_name)

        for x in range(15):
            images.append(imageio.imread(path_name))

        draw_cite_volume(egoG=flower_graph, filename=os.path.join(plot_dir, '{}_bar_{}.png'.format(user_in, year)))

    imageio.mimsave(os.path.join(plot_dir, '{}_flower.gif'.format(user_in)), images)
