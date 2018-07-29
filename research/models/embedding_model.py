'''
General class structure for embedding models

date:   25 July 2018
author: Alexander Soen
'''

import numpy as np

from utils import *


class EmbeddingModel():
    '''
    '''
    def __init__(self):
        ''' Initialize model.
        '''
        self.obj2idx = None 
        self.idx2obj = None 

        self.obj_dim = 0
        self.emb_dim = 0

        self.emb_matrix = None
        self.paper_information = None


    def fit(self, paper_information):
        ''' Fitting processes to generate embedding matrix
        '''
        raise Exception('No fitting function defined')


    def obj_index_to_emb(self, obj_idx):
        '''
        '''
        raise Exception('No index to embedding function defined')


    def objects_to_vec(self, objects):
        ''' Turns a list of objects into a dictionary from object to
            embedded vectors.
        '''
        vec_map = dict()
        for obj in objects:
            if obj in self.obj2idx:
                obj_idx = self.obj2idx[obj]
                vec_map[obj] = self.obj_index_to_emb(obj_idx)
            else:
                vec_map[obj] = None

        return vec_map


    def object_to_vec(self, obj):
        ''' Turns a object into an embedded vector.
        '''
        return self.objects_to_vec([obj])[obj]


    def sim_obj(self, obj1, obj2, sim_calc=cosine_sim):
        ''' Calculates the cosine similarity (default) between two papers given
            their titles.
        '''
        vecs = self.objects_to_vec([obj1, obj2])
        if None in vecs:
            return None
        else:
            return sim_calc(*vecs.values())


    def most_sim(self, vec, k=5, sim_calc=cosine_sim):
        ''' Finds the k most similar (wrt cosine similarity by default) objects
            given an embedded vector.
        '''
        res = list()

        # Vector of similarity scores
        sim_vec = list(map(lambda idx: \
            sim_calc(self.obj_index_to_emb(idx), vec), range(self.obj_dim)))

        top_idx = np.argsort([ -val for val in sim_vec ])[:k]
        for idx in top_idx:
            res.append({'idx': idx, 'obj': self.idx2obj[idx],
                        'sim': sim_vec[idx]})

        return res
