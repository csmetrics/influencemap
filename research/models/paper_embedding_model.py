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
        res = dict()
        for author in authors:
            res[author] = list()

        # Find associated vecs for each author
        for paper_info in self.paper_information:
            for auth_prop in paper_info['Authors']:
                paper_author = auth_prop['AuthorName']
                if paper_author in authors:
                    paper_title = paper_info['PaperTitle']
                    paper_vec = self.title_to_vec(paper_title)
                    # Check for invalid embedding
                    if paper_vec is not None:
                        res[paper_author].append(paper_vec)

        # Create final vectors
        agg_res = dict()
        for author, vecs in res.items():
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
