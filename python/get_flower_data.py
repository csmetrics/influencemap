import sqlite3
import os
import sys
from datetime import datetime
from mkAff import getAuthor
from export_citations import filter_references
from entity_type import *

# Limit number of query
BATCH_SIZE = 999 # MAX=999

# database location
db_dir = "/localdata/u5642715/influenceMapOut"

# output directory
dir_out = "/localdata/u5642715/influenceMapOut/out"

def ids_dict(pdict):
    res = dict()
    for key in pdict.keys():
        res[key] = True
    return res

def get_papers(pdict):
    values = list()
    for key in pdict.keys():
        values += pdict[key]
    return values

def self_dict(pdict):
    res = dict()
    for key in pdict.keys():
        res[key] = True
    return res

'''
def coauthors_dict(conn, pdict, my_e_type, fdict=dict()):
    e_id = pdict.keys()
    paper_ids = get_papers(pdict)
    coauth_dict = fdict

    cur = conn.cursor()

    for paper in paper_ids:
        query = 'SELECT {} FROM paper_info WHERE paper_id = ?'.format(my_e_type.get_keyn())
        
        cur.execute(query, (paper, ))

        e_list = list()
        filter_flag = False

        for line in cur.fetchall():
            key, = line
            e_list.append(key)
            if key in e_id:
                filter_flag = True

        for val in e_list:
            coauth_dict[val] = True

    cur.close()
    return coauth_dict
'''

def get_weight(e_type, qline, ref_count):
    if e_type == Entity.AUTH:
        auth_id, auth_count = qline
        if not auth_id == '':
            return [(auth_id, (1 / auth_count) * (1 / ref_count), e_type.keyn[0])]

    res = list()
    for idx, key in enumerate(e_type.keyn):
        e_id = qline[idx]
        if not e_id == '':
            res.append((e_id, 1 / ref_count, key))
    return res

def try_get(conn, key, qdict, query, qargs, func=lambda x: x):
    try:
        res = qdict[key]
        return res
    except KeyError:
        cur = conn.cursor()
        cur.execute(query, qargs)
        res = func(cur.fetchall())
        qdict[key] = res
        return res
        
def gen_score(conn, e_map, plist, id_to_name, sc_dict, inc_self=False):
    my_type, e_type = e_map.get_map()
    sc_map = lambda f : set(map(lambda r : r[0], f))
    e_map = lambda f : ' '.join(f[0][1].split())

    res = dict()

    # split papers into chunks
    total_prog = 0
    total = len(plist)

    cur = conn.cursor()

    for paper, ref_count, my_paper in plist:
        # Determine if the paper is a self-citation of the orig paper
        skip = False
        if not inc_self:
            for key in my_type.keyn:
                sc_query = 'SELECT {} FROM paper_info WHERE paper_id = ?'.format(key)

                # Find the entities (and cache to dictionary)
                my_e = try_get(conn, my_paper, sc_dict[key], sc_query, (my_paper,), func=sc_map)
                    
                their_e = try_get(conn, paper, sc_dict[key], sc_query, (paper,), func=sc_map)

                # Check if author overlap ie selfcite
                if not my_e.isdisjoint(their_e):
                    skip = True
                    break

        if skip:
            continue

        # query plan finding paper weights
        output_scheme = ",".join(e_type.scheme)
        query = 'SELECT {} FROM paper_info WHERE paper_id = ?'.format(output_scheme)

        cur.execute(query, (paper, ))

        # iterate through query results
        for line in cur.fetchall():
            # iterate over different table types
            for wline in get_weight(e_type, line, ref_count):
                e_id, weight, tkey = wline
                id_query = 'SELECT * FROM {} WHERE {} = ? LIMIT 1'.format(e_type.edict[tkey], tkey)

                e_name = try_get(conn, e_id, id_to_name[tkey], id_query, (e_id, ), func=e_map)

                # Add to score
                try:
                    res[e_name] += weight
                except KeyError:
                    res[e_name] = weight

    cur.close()

    # return dict results
    return res, id_to_name, sc_dict

# Generate the scores
def generate_scores(conn, e_map, citing_p, cited_p, inc_self=False):
    print('\n---\n{} start generating scores\n---'.format(datetime.now()))

    my_type, e_type = e_map.get_map()

    # initial id to name dictionaries 
    id_to_name = dict([(tname, dict()) for tname in e_type.keyn])
    sc_dict = dict([(tname, dict()) for tname in my_type.keyn])

    # Generate scores
    print('{} start generate cited scores'.format(datetime.now()))
    citing_score, id_to_name, sc_dict = gen_score(conn, e_map, citing_p, id_to_name, sc_dict, inc_self=inc_self)
    print('{} finish generate cited scores'.format(datetime.now()))

    print('{} start generate citing scores'.format(datetime.now()))
    cited_score, _, _ = gen_score(conn, e_map, cited_p, id_to_name, sc_dict, inc_self=inc_self)
    print('{} finish generate citing scores'.format(datetime.now()))

    print('---\n{} finish generating scores\n---\n'.format(datetime.now()))

    # return sorted dictionaries
    return citing_score, cited_score

if __name__ == "__main__":

    # input
    name = sys.argv[1]

    # get paper ids associated with input name
    print('{} start get associated papers to input name {}'.format(datetime.now(), name))
    _, id_2_paper_id = getAuthor(name)
    print('{} finish get associated papers to input name {}'.format(datetime.now(), name))

    associated_papers = get_papers(id_2_paper_id)
    my_ids = ids_dict(id_2_paper_id)

    # sqlite connection
    db_path = os.path.join(db_dir, 'paper_info.db')
    conn = sqlite3.connect(db_path)

    db_path2 = os.path.join(db_dir, 'paper_ref.db')
    conn2 = sqlite3.connect(db_path2)

    # filter ref papers
    citing_papers, cited_papers = filter_references(conn2, associated_papers)

    # Generate a self filter dictionary
    filter_dict = self_dict(id_2_paper_id)

    # Add coauthors to filter
    # filter_dict = coauthors_dict(conn, id_2_paper_id, Entity.AUTH, filter_dict)

    # Generate associated author scores for citing and cited
    citing_records, cited_records = generate_scores(conn, Entity_map(Entity.AUTH, Entity.AUTH), citing_papers, cited_papers)

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
