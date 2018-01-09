import operator
import pandas as pd
from entity_type import *
from functools import reduce

weights = {
    'citing authors' : lambda r : 1 / r['citing_auth_count'],
    'cited authors' : lambda r : 1 / r['cited_auth_count'],
    'citing references' : lambda r : 1 / r['citing_rc']
    }

default = {
    'citing authors' : False,
    'cited authors' : False,
    'citing references' : False
    }

def is_weighted(func_name, bval):
    if bval:
        return weights[func_name]
    else:
        return lambda r : 1

def get_weight(e_map, row, tweight=default):
    if row['citing']:
        e_type = e_map.codomain
        e_func = lambda s : 'citing_' + s
    else:
        e_type = e_map.domain
        e_func = lambda s : 'cited_' + s

    res = list()
    if e_type == Entity.AUTH:
        val = reduce(operator.mul, map(lambda v : is_weighted(*v)(row), tweight.items()))
        key = e_type.keyn[0]
        for i, auth_id in row[e_func(key)].iteritems():
            if not auth_id == '':
                res.append((auth_id, val, key))
    else:
        for key in e_type.keyn:
            wname = 'citing references'
            val = is_weighted(wname, tweight[wname])(row)
            e_id = row[e_func(key)]
            if not e_id == '':
                res.append((e_id, val, key))
    return res
