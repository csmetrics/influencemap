import sqlite3
import os
import sys
import pandas as pd
from datetime import datetime
from mkAff import getAuthor
from export_citations import filter_references
from entity_type import *
from flower_helpers import *

# database location
db_dir = "/localdata/u5642715/influenceMapOut"

# output directory
dir_out = "/localdata/u5642715/influenceMapOut/out"

info_cols = ['auth_id', 'num_auth', 'conf_id', 'journ_id', 'affi_id']
mult_cols = [0]

def auth_weight(row):
    res = list()
    if row['citing']:
        val = (1 / row['citing_auth_count']) * (1 / row['citing_rc'])
        for auth_id in row['citing_auth_id']:
            if not auth_id == '':
                res.append((auth_id, val))
    else:
        val = (1 / row['citing_auth_count']) * (1 / row['citing_rc'])
        for i, auth_id in row['cited_auth_id'].iteritems():
            if not auth_id == '':
                res.append((auth_id, val))
    return res

def get_weight(e_map, row):
    if row['citing']:
        e_type = e_map.codomain
        e_func = lambda s : 'citing_' + s
    else:
        e_type = e_map.domain
        e_func = lambda s : 'cited_' + s

    res = list()
    if e_type == Entity.AUTH:
        auth_res = auth_weight(row)
        res += map(lambda r : r + (e_type.keyn[0], ), auth_res)
    else:
        for key in e_type.keyn:
            e_id = row[e_func(key)]
            if not e_id == '':
                res.append((e_id, 1 / row['citing_rc'], key))
    return res
    

def generate_scores(conn, e_map, data_df, inc_self=False):

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
            for wline in get_weight(e_map, row):
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

    # Input data directory
    data_dir = '/mnt/data/MicrosoftAcademicGraph'

    # Output data directory
    out_dir = '/localdata/u5642715/influenceMapOut'

    # database output directory
    db_dir = '/localdata/u5642715/influenceMapOut'

    # get paper ids associated with input name
    _, id_2_paper_id = getAuthor(user_in)

    db_path = os.path.join(db_dir, 'paper_info2.db')
    conn = sqlite3.connect(db_path)

    data_df = gen_search_df(conn, id_2_paper_id)

    influence_dict = generate_scores(conn, Entity_map(Entity.AUTH, Entity.AUTH), data_df, inc_self=True)
    citing_records = influence_dict['influenced']
    cited_records = influence_dict['influencing']

    # sorter
    sort_by_value = lambda d : sorted(d.items(), key=lambda kv : (kv[1] ,kv[0]), reverse=True)

    # Print to file (Do we really need this?)
    with open(os.path.join(dir_out, 'authors_citing.txt'), 'w') as fh:
        for key, val in sort_by_value(citing_records):
            fh.write("{}\t{}\n".format(key, val))

    with open(os.path.join(dir_out, 'authors_cited.txt'), 'w') as fh:
        for key, val in sort_by_value(cited_records):
            fh.write("{}\t{}\n".format(key, val))

    conn.close()
