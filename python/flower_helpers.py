import sqlite3

def get_papers(pdict):
    values = list()
    for key in pdict.keys():
        values += pdict[key]
    return values

def try_get(conn, key, qdict, query, func=lambda x: x):
    try:
        return qdict[key]
    except KeyError:
        cur = conn.cursor()
        cur.execute(query, (key, ))
        res = func(cur.fetchall())
        qdict[key] = res
        return res

def is_selfcite(conn, paper_id, paper_ref_id, auth_dict):
    sc_query = 'SELECT auth_id FROM paper_info WHERE paper_id = ?'
    func = lambda f : set(map(lambda r : r[0], f))

    my_auth = try_get(conn, paper_id, auth_dict, sc_query, func=func)
                    
    their_auth = try_get(conn, paper_ref_id, auth_dict, sc_query, func=func)

    return int(not my_auth.isdisjoint(their_auth))
