'''
'''

from paper_embedding_model import PaperEmbeddingModel
from scipy.sparse          import csr_matrix
from utils                 import *

import numpy as np


class InversePaperFreq(PaperEmbeddingModel):
    '''
    '''
    def __init__(self, link_dir=None):
        ''' Initialize model.
        '''
        PaperEmbeddingModel.__init__(self)
        self.venue2idx = None 
        self.idx2venue = None 

        self.link_dir = 'Citations' if link_dir == 'Citations' else 'References'


    def fit(self, paper_information):
        ''' Fitting processes. Generates the term frequency matrix.
        '''
        # Re-init values
        self.obj2idx = dict()
        self.idx2obj = dict()

        self.venue2idx = dict()
        self.idx2venue = dict()

        self.obj_dim = 0
        self.emb_dim = 0

        # Save paper information
        self.paper_information = paper_information

        # csr matrix values
        indptr = [0]
        indices = []
        data = []

        for paper_info in paper_information:
            # Skip paper information for ones with no information
            if not paper_info[self.link_dir]:
                continue

            # Generate paper index maps
            paper_title = paper_info['PaperTitle']
            if paper_title not in self.obj2idx:
                self.obj2idx[paper_title]    = self.obj_dim
                self.idx2obj[self.obj_dim]   = paper_title

                self.obj_dim += 1
                
            # Find all venues
            for ref_prop in paper_info[self.link_dir]:
                if 'ConferenceName' in ref_prop:
                    venue = ref_prop['ConferenceName']
                elif 'JournalName' in ref_prop:
                    venue = ref_prop['JournalName']
                else:
                    continue
                
                # Add if venue not in map
                if venue not in self.venue2idx:
                    self.venue2idx[venue]        = self.emb_dim
                    self.idx2venue[self.emb_dim] = venue

                    self.emb_dim += 1
            
                # Get the venue index
                venue_idx = self.venue2idx[venue]

                # csr update
                indices.append(venue_idx)
                data.append(1)

            # csr update
            indptr.append(len(indices))

        # Generate tf matrix
        self.tf_matrix = csr_matrix((data, indices, indptr), dtype=int)

        df_matrix = self.tf_matrix.sign()
        self.idf_vector = np.log(self.obj_dim / df_matrix.sum(axis=0))
        self.idf_vector = np.array(self.idf_vector)[0]

        self.emb_matrix = self.tf_matrix.multiply(self.idf_vector)


    def obj_index_to_emb(self, obj_idx):
        '''
        '''
        return self.emb_matrix.getrow(obj_idx).toarray()[0]


    def authors_to_vec(self, authors, scoring='sum'):
        ''' Calculates the embedded vector for authors through the aggregation
            of the paper vectors associated to the author.
        '''
        # Get the author indices
        auth_indices = find_author_indices(authors, self.paper_information,
                self.obj2idx)

        # Turn indices into embedding vectors
        idx_to_tf = lambda i: np.array(self.tf_matrix.getrow(i).toarray()[0])
        to_emb_vecs = lambda x_list: [idx_to_tf(x) for x in x_list \
                if idx_to_tf is not None]
        res = [(a, to_emb_vecs(idx)) for a, idx in auth_indices.items()]

        # Create final vectors
        agg_res = dict()
        for author, vecs in res:
            if not vecs:
                agg_res[author] = None
            elif scoring == 'avg':
                agg_res[author] = np.multiply(np.mean(vecs, axis=0),
                        self.idf_vector)
            else:
                agg_res[author] = np.multiply(np.sum(vecs, axis=0),
                        self.idf_vector)

        return agg_res
