import operator
import pandas as pd
from entity_type import *
from functools import reduce

weights = {
    'citing authors' : lambda r : 1 / r['auth_count_citing'],
    'cited authors' : lambda r : 1 / r['auth_count_cited'],
    'citing references' : lambda r : 1 / r['rc_citing']
    }

default = {
    'citing authors' : False,
    'cited authors' : True,
    'citing references' : False
    }

def is_weighted(func_name, bval):
    if bval:
        return weights[func_name]
    else:
        return lambda r : 1

def get_weight(e_map, row, tweight=default):
    if row['citing']:
        e_func = lambda s :  s + '_citing'
    else:
        e_func = lambda s : s + '_cited'
    e_type = e_map.codomain

    res = list()
    if e_type == Entity.AUTH:
        val = reduce(operator.mul, map(lambda v : is_weighted(*v)(row), tweight.items()))
        key = e_type.keyn[0]
        for auth_name in row[e_func(key)].split(','):
            if not auth_name == '':
                res.append((auth_name, val, key))
    else:
        for key in e_type.keyn:
            wname = 'citing references'
            val = is_weighted(wname, tweight[wname])(row)
            e_name = row[e_func(key)]
            if not e_name == '':
                res.append((e_name, val, key))
    return res
