'''
Utility functions for models

date:   25 July 2018
author: Alexander Soen
'''

import numpy as np


def get_norm(v):
    ''' Faster than numpy linalg
    '''
    return np.sqrt((v*v).sum())


def cosine_sim(v1, v2):
    ''' Calculates cosine similarity.
    '''
    return np.dot(v1, v2) / (get_norm(v1) * get_norm(v2))


def gen_cmp_matrix(vec_list, calc=cosine_sim):
    ''' Calculate a comparison matrix between vectors in the list.
    '''
    n = len(vec_list)
    cmp_matrix = np.ones((n, n))

    # Calculate comparison per vector combination
    for i in range(n):
        for j in range(n):
            cmp_matrix[i, j] = calc(vec_list[i], vec_list[j])

    return cmp_matrix
