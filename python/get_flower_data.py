import sqlite3
import os
import sys
import pandas as pd
from datetime import datetime
from mkAff import getAuthor
from entity_type import *
from flower_helpers import *
from influence_weight import get_weight

# Config setup
from config import *

def generate_scores(conn, e_map, data_df, inc_self=False, calc_weight=get_weight):
    print('{} start score generation\n---'.format(datetime.now()))
    df = pd.concat(data_df.values())
    if not inc_self:
        df = df.loc[df['self_cite'] == 0]

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
                e_id, weight, tkey = wline

                id_query = 'SELECT * FROM {} WHERE {} = ? LIMIT 1'.format(e_type.edict[tkey], tkey)

                e_name = try_get(conn, e_id, id_to_name[tkey], id_query, func=id_query_map)

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

if __name__ == "__main__":
    from mkAff import getAuthor
    from get_flower_df import gen_search_df
    import os, sys

    # input
    user_in = sys.argv[1]

    # get paper ids associated with input name
    _, id_2_paper_id = getAuthor(user_in)

    conn = sqlite3.connect(DB_PATH)

    data_df = gen_search_df(conn, id_2_paper_id)

    influence_dict = generate_scores(conn, Entity_map(Entity.AUTH, Entity.CONF), data_df, inc_self=True)
    citing_records = influence_dict['influenced']
    cited_records = influence_dict['influencing']

    # sorter
    sort_by_value = lambda d : sorted(d.items(), key=lambda kv : (kv[1] ,kv[0]), reverse=True)

    # Print to file (Do we really need this?)
    with open(os.path.join(OUT_DIR, 'authors_citing.txt'), 'w') as fh:
        for key, val in sort_by_value(citing_records):
            fh.write("{}\t{}\n".format(key, val))

    with open(os.path.join(OUT_DIR, 'authors_cited.txt'), 'w') as fh:
        for key, val in sort_by_value(cited_records):
            fh.write("{}\t{}\n".format(key, val))

    conn.close()
