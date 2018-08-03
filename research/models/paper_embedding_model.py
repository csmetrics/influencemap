'''
'''

import numpy as np

from embedding_model import EmbeddingModel
from utils import *


class PaperEmbeddingModel(EmbeddingModel):
    '''
    '''
    def titles_to_vec(self, titles):
        ''' Turns a list of paper titles into a dictionary from titles to
            embedded vectors.
        '''
        return self.objects_to_vec(titles)


    def title_to_vec(self, title):
        ''' Turns a paper title into an embedded vector.
        '''
        return self.object_to_vec(title)


    def sim_titles(self, title1, title2, sim_calc=cosine_sim):
        ''' Calculates the cosine similarity (default) between two papers given
            their titles.
        '''
        return self.sim_obj(title1, title2, sim_calc=cosine_sim)


    def authors_to_vec(self, authors, scoring='sum'):
        ''' Calculates the embedded vector for authors through the aggregation
            of the paper vectors associated to the author.
        '''
        # Get the author indices
        auth_indices = find_author_indices(authors, self.paper_information,
                self.obj2idx)

        # Turn indices into embedding vectors
        to_emb_vecs = lambda x_list: [self.obj_index_to_emb(x) for x in x_list \
                if self.obj_index_to_emb is not None]
        res = [(a, to_emb_vecs(idx)) for a, idx in auth_indices.items()]

        # Create final vectors
        agg_res = dict()
        for author, vecs in res:
            print(vecs)
            if not vecs:
                agg_res[author] = None
            elif scoring == 'avg':
                agg_res[author] = np.mean(vecs, axis=0)
            else:
                agg_res[author] = np.sum(vecs, axis=0)

        return agg_res


    def author_to_vec(self, author, scoring='sum'):
        ''' Calculate the embedding vector for an author.
        '''
        return self.authors_to_vec([author], scoring=scoring)[author]
