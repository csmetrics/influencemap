import sqlite3
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from mkAff import getAuthor
from entity_type import *
from flower_helpers import *
from influence_weight import get_weight

# Config setup
from config import *

# Creates dictionaries for the weight scores
def generate_scores(conn, e_map, data_df, inc_self=False, calc_weight=get_weight):
    print('{} start score generation\n---'.format(datetime.now()))

    # Concat the tables together
    df = pd.concat(data_df.values())

    # Check self citations
    if not inc_self:
        df = df.loc[df['self_cite'].fillna(False)]

    my_type, e_type = e_map.get_map()
    id_query_map = lambda f : ' '.join(f[0][1].split())
    id_to_name = dict([(tname, dict()) for tname in e_type.keyn])

    # query plan finding paper weights
    output_scheme = ",".join(e_type.scheme)
    query = 'SELECT {} FROM paper_info WHERE paper_id = ?'.format(output_scheme)

    res = {'influencing' : dict(), 'influenced': dict()}
    
    cur = conn.cursor()

    for i, row in df.iterrows():
            # iterate over different table types
            for wline in calc_weight(e_map, row):
                e_name, weight, tkey = wline

                # Add to score
                if row['citing']:
                    try:
                        res['influenced'][e_name] += weight
                    except KeyError:
                        res['influenced'][e_name] = weight
                else:
                    try:
                        res['influencing'][e_name] += weight
                    except KeyError:
                        res['influencing'][e_name] = weight

    print('{} finish score generation\n---'.format(datetime.now()))
    return res

# Generates pandas dataframe for scores
def generate_score_df(influence_dict, ratio_func=np.vectorize(lambda x, y : x / y), sort_func=np.maximum):
    df_dict = list()

    # Turn influence dictionaries into an outer merged table
    for tkey, data_dict in influence_dict.items():
        df_dict.append(pd.DataFrame.from_records(list(data_dict.items()), columns=['entity_id', tkey]))
    score_df = pd.merge(*df_dict, how='outer', on='entity_id', sort=False)

    # calculate minimum scores to fill nan values (for ratio)
    nan_influenced = score_df['influenced'].min() / 2
    nan_influencing = score_df['influenced'].min() / 2

    score_df['influenced'].fillna(nan_influenced, inplace=True)
    score_df['influencing'].fillna(nan_influencing, inplace=True)

    # calculate sum
    score_df['sum'] = score_df['influenced'] + score_df['influencing']

    # calculate influence ratios
    score_df['ratio'] = ratio_func(score_df['influenced'], score_df['influencing'])

    # sort by union max score
    score_df = score_df.assign(tmp = sort_func(score_df['influencing'], score_df['influenced']))
    score_df = score_df.sort_values('tmp', ascending=False).drop('tmp', axis=1)

    return score_df

if __name__ == "__main__":
    from mkAff import getAuthor
    from get_flower_df import gen_search_df
    import os, sys

    # input
    #user_in = sys.argv[1]

    # get paper ids associated with input name
    #_, id_2_paper_id = getAuthor(user_in)

    id_2_paper_id = {}

    conn = sqlite3.connect(DB_PATH)

    data_df = gen_search_df(conn, id_2_paper_id)

    influence_dict = generate_scores(conn, Entity_map(Entity.AUTH, Entity.CONF), data_df, inc_self=True)
    print(generate_score_df(influence_dict))
    #citing_records = influence_dict['influenced']
    #cited_records = influence_dict['influencing']

    ## sorter
    #sort_by_value = lambda d : sorted(d.items(), key=lambda kv : (kv[1] ,kv[0]), reverse=True)

    ## Print to file (Do we really need this?)
    #with open(os.path.join(OUT_DIR, 'authors_citing.txt'), 'w') as fh:
    #    for key, val in sort_by_value(citing_records):
    #        fh.write("{}\t{}\n".format(key, val))

    #with open(os.path.join(OUT_DIR, 'authors_cited.txt'), 'w') as fh:
    #    for key, val in sort_by_value(cited_records):
    #        fh.write("{}\t{}\n".format(key, val))

    conn.close()
