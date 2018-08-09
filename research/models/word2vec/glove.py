''' Glove title embedding
'''

import torch
import torch.nn            as nn
import torch.nn.functional as F


class GloVe(nn.Module):


    def __init__(self, emb_size, emb_dim, cooc, x_max=100, alpha=3/4):
        '''
        '''
        super().__init__()
        self.emb_size = emb_size
        self.emb_dim  = emb_dim

        # Embeddings
        self.w_embedding = nn.Embedding(emb_size, emb_dim)
        self.c_embedding = nn.Embedding(emb_size, emb_dim)

        # Bias factor
        self.w_bias = torch.randn((emb_size, 1), requires_grad=True)
        self.c_bias = torch.randn((emb_size, 1), requires_grad=True)

        # Coocurrance matrix
        self.coocurrance = torch.FloatTensor(cooc) # Sparseness???

        # Weight function attributes
        self.x_max = x_max
        self.alpha = alpha


    def forward(self, w_idx, c_idx):
        '''
        '''
        # Tensor indices
        w_t_idx = torch.LongTensor(w_idx)
        c_t_idx = torch.LongTensor(c_idx)

        # Embedding vectors
        w_vec = self.w_embedding(w_idx)
        c_vec = self.c_embedding(c_idx)

        # Bias values
        w_bias = self.w_bias[w_idx]
        c_bias = self.c_bias[c_idx]

        # Co-occurance count
        cc = self.coocurrance[w_idx, c_idx].unsqueeze(1)

        # Weight function
        wf = torch.clamp(torch.pow(cc / self.x_max, self.alpha), max=1)

        loss = torch.sum(wf*(w_vec*c_vec + w_bias + c_bias - torch.log(cc))**2)

        return loss
