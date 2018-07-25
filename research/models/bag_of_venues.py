'''
Class for bag of venues model

TODO: Add pca projection as function

date:   25 July 2018
author: Alexander Soen
'''

from scipy.sparse import csr_matrix
from utils        import *

import numpy as np


class BagOfVenues():
    def __init__(self, link_dir=None):
        self.title2idx = None 
        self.idx2title = None 

        self.venue2idx = None 
        self.idx2venue = None 

        self.title_dim = 0
        self.venue_dim = 0

        self.link_dir = 'Citations' if link_dir == 'Citations' else 'References'
        self.tf_matrix = None


    def fit(self, paper_information):
        # Re-init values
        self.title2idx = dict()
        self.idx2title = dict()

        self.venue2idx = dict()
        self.idx2venue = dict()

        self.title_dim = 0
        self.venue_dim = 0

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
            if paper_title not in self.title2idx:
                self.title2idx[paper_title]      = self.title_dim
                self.idx2title[self.title_dim]   = paper_title

                self.title_dim += 1
                
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
                    self.venue2idx[venue]          = self.venue_dim
                    self.idx2venue[self.venue_dim] = venue

                    self.venue_dim += 1
            
                # Get the venue index
                venue_idx = self.venue2idx[venue]

                # csr update
                indices.append(venue_idx)
                data.append(1)

            # csr update
            indptr.append(len(indices))

        # Generate tf matrix
        self.tf_matrix = csr_matrix((data, indices, indptr), dtype=int)


    def titles_to_vec(self, titles):
        '''
        '''
        vec_map = dict()
        for title in titles:
            if title in self.title2idx:
                title_idx = self.title2idx[title]
                vec_map[title] = self.tf_matrix.getrow(title_idx).toarray()[0]
            else:
                vec_map[title] = None

        return vec_map


    def title_to_vec(self, title):
        '''
        '''
        return self.titles_to_vec([title])[title]


    def sim_titles(self, title1, title2):
        '''
        '''
        vecs = self.titles_to_vec([title1, title2])
        if None in vecs:
            return None
        else:
            return cosine_sim(*vecs.values())


    def most_sim(self, vec, k=5):
        '''
        '''
        res = list()

        # Vector of similarity scores
        sim_vec = list(map(lambda paper: cosine_sim(paper.toarray(), vec)[0],
                           self.tf_matrix))

        top_idx = np.argsort([ -val for val in sim_vec ])[:k]
        for idx in top_idx:
            res.append({'idx': idx, 'title': self.idx2title[idx],
                        'sim': sim_vec[idx]})

        return res


    def authors_to_vec(self, authors, scoring='sum'):
        '''
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
                    res[paper_author].append(self.title_to_vec(paper_title))

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
        '''
        '''
        return self.authors_to_vec([author], scoring=scoring)[author]
