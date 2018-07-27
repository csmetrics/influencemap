'''
Utility functions for models

date:   25 July 2018
author: Alexander Soen
'''

import numpy        as np

def get_norm(v):
    ''' Faster than numpy linalg
    '''
    return np.sqrt((v*v).sum())


def cosine_sim(v1, v2):
    '''
    '''
    return np.dot(v1, v2) / (get_norm(v1) * get_norm(v2))

