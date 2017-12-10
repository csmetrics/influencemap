import os, sys
import pandas as pd
from datetime import datetime 
import numpy as np
#import matplotlib.pyplot as plt
import networkx as nx
#import pickle
#import json
from draw_egonet import draw_halfcircle
# initilize plotting packages: seaborn

#import seaborn as sns
#import matplotlib.pyplot as plt
#sns.set()


def print_list(ls):
	for line in ls:
		print(line)
person_of_interest = "brian anderson"

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
top_n_cited = list(cited_df.head(n))
print_list(top_n_cited)

citing_df.sort_values('citingScore', ascending=False)
top_n_citing = list(citing_df.head(n))
print_list(top_n_citing)

# build a graph structure for the top data
personG = nx.DiGraph()

for index, row in cited_df.head(n).iterrows():
	personG.add_edge(person_of_interest, row['authorName'], weight=float(row['citedScore']))

for index, row in citing_df.head(n).iterrows():
	personG.add_edge(row['authorName'], person_of_interest, weight=float(row['citedScore']))


fig = plt.figure(figsize=(24, 6))
ax1 = fig.add_subplot(121)
ax2 = fig.add_subplot(122)
draw_halfcircle(graph=personG, ego=person_of_interest, direction='out', ax=ax1)
draw_halfcircle(graph=personG, ego=person_of_interest, direction='in', ax=ax1)



