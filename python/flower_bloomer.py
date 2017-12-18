import sqlite3
import os, sys
from datetime import datetime
from get_flower_data_memory import gen_score
from export_citations_author import construct_cite_db
import pandas as pd
import numpy as np
import networkx as nx
from draw_egonet import draw_halfcircle
import seaborn as sns
import matplotlib.pyplot as plt
sns.set()
plt.switch_backend('agg')


def getFlower(papers, name):
    print("papers {}, name {}".format(papers, name))
    # db_dir = '/localdata/u5/influencemap'
    db_dir = "/localdata/u5642715/influenceMapOut"
    #db_name = 'paper.db'
    #db_path = os.path.join(db_dir, db_name)
    db_path = os.path.join(db_dir, 'paper_info.db')
    dir_out = '/localdata/u5798145/influencemap/out'

    paperIDs = list(set(papers))

    citing_papers, cited_papers = construct_cite_db(name, paperIDs)
    
    conn = sqlite3.connect(db_path)

    # Generate associated author scores for citing and cited
    citing_records = gen_score(conn, citing_papers)
    cited_records = gen_score(conn, cited_papers)
    print(citing_records)

    # Print to file (Do we really need this?
    with open(os.path.join(dir_out, 'authors_citing.txt'), 'w') as fh:
        for key in citing_records.keys():
            fh.write("{}\t{}\n".format(key, citing_records[key]))

    with open(os.path.join(dir_out, 'authors_cited.txt'), 'w') as fh:
        for key in cited_records.keys():
            fh.write("{}\t{}\n".format(key, cited_records[key]))

    conn.close()

    #### START PRODUCING GRAPH
 

    plot_dir = os.path.join(dir_out, 'figures')

    for dir in [dir_out, plot_dir]:
      if not os.path.exists(dir):
          os.makedirs(dir)


    # load data into dataframe
    cited_df = pd.read_csv(os.path.join(dir_out, 'authors_cited.txt'), sep='\t', header=None, names=['authorName', 'citedScore'])

    citing_df = pd.read_csv(os.path.join(dir_out, 'authors_citing.txt'), sep='\t', header=None, names=['authorName', 'citingScore'])

    # get the top x influencers
    n = 25
    cited_df = cited_df.sort_values(by=['citedScore'], ascending=False)
    top_n_cited = list(cited_df.head(n))

    citing_df = citing_df.sort_values(by=['citingScore'], ascending=False)
    top_n_citing = list(citing_df.head(n))

    # build a graph structure for the top data
    personG = nx.DiGraph()

    for index, row in cited_df.head(n).iterrows():
      personG.add_edge(name, row['authorName'], weight=float(row['citedScore']))

    for index, row in citing_df.head(n).iterrows():
      personG.add_edge(row['authorName'], name, weight=float(row['citingScore']))
    
    influencedby_filename = os.path.join(plot_dir, 'influencedby.png')
    influencedto_filename = os.path.join(plot_dir, 'influencedto.png')

    draw_halfcircle(graph=personG, ego=name, renorm_weights='log', direction='in', filename = influencedby_filename)
    draw_halfcircle(graph=personG, ego=name, renorm_weights='log', direction='out', filename = influencedto_filename)

    return influencedby_filename, influencedto_filename




