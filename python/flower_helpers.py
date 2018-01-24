import sqlite3

def get_papers(pdict):
    values = list()
    for key in pdict.keys():
        values += pdict[key]
    return values

def is_self_cite(row, e_id_name, entity_id):
    if row['citing']:
        return not set(entity_id).isdisjoint(set(row[e_id_name + '_citing']))
    else:
        return not set(entity_id).isdisjoint(set(row[e_id_name + '_cited']))
