'''
Utility functions for embedding models.

Date:   9 August 2018
Author: Alexander Soen
'''

import numpy as np

from torch.utils import data


# TITLES

class TitlePreprocess():
    ''' Preprocesser class for title context
    '''

    def __init__(self, paper_information):
        '''
        '''
        titles = list()
        for paper_info in paper_information:
            # Check if in the information dict
            if 'PaperTitle' in paper_info:
                titles.append(paper_info['PaperTitle'])

        # Sample information
        self.titles = titles
        self.pairs  = None

        self.unigram      = None
        self.unigram_dict = dict()
        self.cooc         = None

        # Index dictionaries
        self.word2idx = None


    def title_to_pairs(self, string):
        ''' Turns titles into index pairs
        '''
        words = list(set(string.split()))
        pairs = list()
        for i in range(len(words)):
            idx_i = self.word2idx.setdefault(words[i], len(self.word2idx))

            # Update unigram
            if idx_i in self.unigram_dict:
                self.unigram_dict[idx_i] += 1
            else:
                self.unigram_dict[idx_i] = 1

            for j in range(0, i):
                idx_j = self.word2idx.setdefault(words[j], len(self.word2idx))
                pairs.append((idx_i, idx_j))

            for j in range(i+1, len(words)):
                idx_j = self.word2idx.setdefault(words[j], len(self.word2idx))
                pairs.append((idx_i, idx_j))

        return pairs


    def gen_pairs(self):
        '''
        '''
        # Initit the indexing dictionary
        self.word2idx = dict()
        
        pairs = list()
        for title in self.titles:
            pairs += self.title_to_pairs(title)

        self.pairs = pairs
        return pairs


    def gen_cooc(self):
        '''
        '''
        cooc = np.zeros((len(self.word2idx), len(self.word2idx)))
        for title in self.titles:
            words = list(set(title.split()))
            for i in range(len(words)):
                for j in range(i+1, len(words)):
                    i_idx = self.word2idx[words[i]]
                    j_idx = self.word2idx[words[j]]

                    cooc[i_idx, j_idx] += 1
                    cooc[j_idx, i_idx] += 1

        self.cooc = cooc
        return cooc


    def gen_unigram(self):
        '''
        '''
        return NotImplemented


class TitleWordCorpus(data.Dataset):
    ''' Generate corpus for word pairs in the title
    '''
    def __init__(self, pair_data):
        '''
        '''
        self.data = pair_data


    def __len__(self):
        return len(self.data)


    def __getitem__(self, idx):
        return self.data[idx]
