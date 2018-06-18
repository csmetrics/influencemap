import operator
import pandas as pd
from core.search.entity_type import *
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

def get_weight(row, tweight=default):
    return reduce(operator.mul, map(lambda v : is_weighted(*v)(row), tweight.items()))
