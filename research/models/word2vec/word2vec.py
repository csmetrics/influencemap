'''
'''

import pickle
import torch
import torch.nn            as nn
import torch.nn.functional as F
import numpy               as np

from torch.utils.data import Dataset


class Preprocess():


    def __init__(self, paper_information):
        '''
        '''
        titles = list()
        for paper_info in paper_information:
            titles.append(paper_info['PaperTitle'])

        self.titles = titles
        self.pairs  = None
        self.index  = None

        self.unigram = None
        self.unigram_dict = dict()


    def string_to_pairs(self, string):
        '''
        '''
        words = list(set(string.split()))
        pairs = list()
        for i in range(len(words)):
            idx_i = self.index.setdefault(words[i], len(self.index))

            # Update unigram
            if idx_i in self.unigram_dict:
                self.unigram_dict[idx_i] += 1
            else:
                self.unigram_dict[idx_i] = 1

            for j in range(0, i):
                idx_j = self.index.setdefault(words[j], len(self.index))
                pairs.append((idx_i, idx_j))

            for j in range(i+1, len(words)):
                idx_j = self.index.setdefault(words[j], len(self.index))
                pairs.append((idx_i, idx_j))

        return pairs


    def gen_pairs(self):
        '''
        '''
        self.index = dict()

        pairs = list()
        for title in self.titles:
            pairs += self.string_to_pairs(title)

        self.pairs = pairs
        return pairs


    def gen_unigram(self):
        '''
        '''
        unigram = np.zeros(len(self.unigram_dict), dtype=int)
        for key, val in self.unigram_dict.items():
            unigram[key] = val

#        unigram = unigram / unigram.sum()
        self.unigram = unigram
        return unigram


    def export_pairs(self, file_path):
        '''
        '''
        with open(file_path, 'wb') as f:
            pickle.dump(self.pairs, f)


    def export_unigram(self, file_path):
        '''
        '''
        with open(file_path, 'wb') as f:
            pickle.dump(self.unigram, f)



class ContextCorpus(Dataset):


    def __init__(self, data_path):
        '''
        '''
        self.data = pickle.load(open(data_path, 'rb'))


    def __len__(self):
        return len(self.data)


    def __getitem__(self, idx):
        return self.data[idx]


class UnigramCorpus(Dataset):
    ''' Temp solution
    '''

    def __init__(self, unigram):
        z = unigram.sum()
        data = np.zeros(z * 20, dtype=int)
        for i, value in enumerate(unigram):
            for j in range(20):
                data[i + j * z] = value

        self.data = data


    def __len__(self):
        return len(self.data)


    def __getitem__(self, idx):
        return self.data[idx]


class SGNS(nn.Module):


    def __init__(self, emb_size, emb_dim):
        '''
        '''
        super().__init__()
        self.emb_size = emb_size
        self.emb_dim  = emb_dim

        # Embeddings
        self.w_embedding = nn.Embedding(emb_size, emb_dim)
        self.c_embedding = nn.Embedding(emb_size, emb_dim)


    def forward(self, pos_w_idx, pos_c_idx, neg_w_idx, neg_c_idx):
        '''
        '''
        # Get the embeddings
        pos_w_vec = self.w_embedding(torch.LongTensor(pos_w_idx))
        pos_c_vec = self.w_embedding(torch.LongTensor(pos_c_idx))
        neg_w_vec = self.w_embedding(torch.LongTensor(neg_w_idx))
        neg_c_vec = self.w_embedding(torch.LongTensor(neg_c_idx))

        # Calculate objective function for pos and neg
        pos_loss = torch.mul(pos_w_vec, pos_c_vec)
        pos_loss = torch.sum(pos_loss, 1) # Sum columns together
        pos_loss = F.logsigmoid(pos_loss)
        pos_loss = torch.sum(pos_loss)

        neg_loss = torch.mul(neg_w_vec, neg_c_vec)
        neg_loss = torch.sum(neg_loss, 1)
        neg_loss = torch.neg(neg_loss)
        neg_loss = F.logsigmoid(neg_loss)
        neg_loss = torch.sum(neg_loss)

        # Turn objective funtion to a loss
        total_loss = torch.neg(pos_loss + neg_loss)

        return total_loss
