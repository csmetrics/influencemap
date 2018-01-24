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
#    e_type = e_map.codomain

#    if e_type == Entity.AUTH:
    return reduce(operator.mul, map(lambda v : is_weighted(*v)(row), tweight.items()))
#    else:
#        wname = 'citing references'
#        return is_weighted(wname, tweight[wname])(row)
