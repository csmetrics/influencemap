import os, sys
import pandas as pd
from datetime import datetime 
import numpy as np
#import matplotlib.pyplot as plt
#import networkx as nx
#import pickle
#import json

# initilize plotting packages: seaborn

#import seaborn as sns
#import matplotlib.pyplot as plt
#sns.set()

conf = 'PLDI'

data_dir = '/localdata/u5798145/influencemap/out' 
out_dir = '/localdata/u5798145/influencemap/out'

plot_dir = os.path.join(out_dir, 'figures')

for dir in [data_dir, out_dir, plot_dir]:
	if not os.path.exists(dir):
	    os.makedirs(dir)


# load data into dataframe
cited_df = pd.read_csv(os.path.join(data_dir, 'authors_cited.txt'), sep='\t', header=None)
cited_df.columns = ['authorName', 'citedScore']

citing_df = pd.read_csv(os.path.join(data_dir, 'authors_citing.txt'), sep='\t', header=None)
citing_df.columns = ['authorName', 'citingScore']

# get the top x influencers
n = 25
cited_df.sort_values('citedScore', ascending=False)
top_n_cited = list(cited_df['authorName'].head(n))
print(top_n_cited)


# build a graph structure for the top data
#personG = nx.DiGraph()


