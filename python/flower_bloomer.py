# standard python imports
import sqlite3
import os, sys
from datetime import datetime
import pandas as pd
import numpy as np
import networkx as nx
import seaborn as sns
import matplotlib.pyplot as plt
sns.set()
plt.switch_backend('agg')

# local module imports
from get_flower_data_memory import *
from export_citations_author import construct_cite_db
from draw_egonet import draw_halfcircle
from entity_type import Entity


entity_type_dict = {'author': Entity.AUTH, 'conf': Entity.CONF, 'institution': Entity.AFFI}


def getFlower(id_2_paper_id, name, ent_type):
    # db_dir = '/localdata/u5/influencemap'
    db_dir = "/localdata/u5642715/influenceMapOut"
    #db_name = 'paper.db'
    #db_path = os.path.join(db_dir, db_name)
    db_path = os.path.join(db_dir, 'paper_info.db')
    dir_out = '/localdata/u5798145/influencemap/out'


    # get paper ids associated with input name
    print("\n\nid_to_paper_id\n\n\n\n\n\n{}".format(id_2_paper_id))

    #if ent_type == "conf":
    #    associated_papers = 
    associated_papers = get_papers(id_2_paper_id)
    my_ids = ids_dict(id_2_paper_id)
    print("\n\nassociated papers\n\n\n\n\n\n{}".format(associated_papers))
    # filter ref papers
    print('{} start filter paper references'.format(datetime.now()))
    citing_papers, cited_papers = construct_cite_db(name, associated_papers)
    print('{} finish filter paper references'.format(datetime.now()))

    db_path = os.path.join(db_dir, 'paper_info.db')
    conn = sqlite3.connect(db_path)

    # Generate a self filter dictionary
    filter_dict = self_dict(id_2_paper_id)

    # Add coauthors to filter
    # filter_dict = coauthors_dict(conn, id_2_paper_id, Entity.AUTH, filter_dict)

    # Generate associated author scores for citing and cited
    citing_records = gen_score(conn, entity_type_dict[ent_type], citing_papers, my_ids, fdict=filter_dict)
    cited_records = gen_score(conn, entity_type_dict[ent_type], cited_papers, my_ids, fdict=filter_dict)

    # Print to file (Do we really need this?
    with open(os.path.join(dir_out, 'authors_citing.txt'), 'w') as fh:
        for key in citing_records.keys():
            fh.write("{}\t{}\n".format(key, citing_records[key]))

    with open(os.path.join(dir_out, 'authors_cited.txt'), 'w') as fh:
        for key in cited_records.keys():
            fh.write("{}\t{}\n".format(key, cited_records[key]))
    print("finished writing files")
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
      # note that edge direction is with respect to influence, not citation i.e. for add_edge(a,b,c) it means a influenced b with a weight of c 
      personG.add_edge(row['authorName'], name, weight=float(row['citedScore']))

    for index, row in citing_df.head(n).iterrows():
      personG.add_edge(name, row['authorName'], weight=float(row['citingScore']))
    
    influencedby_filename = os.path.join(plot_dir, 'influencedby.png')
    influencedto_filename = os.path.join(plot_dir, 'influencedto.png')
    print("drawing graphs")
    draw_halfcircle(graph=personG, ego=name, renorm_weights='log', direction='in', filename = influencedby_filename)
    draw_halfcircle(graph=personG, ego=name, renorm_weights='log', direction='out', filename = influencedto_filename)
    print("finished graphs")
    return influencedby_filename, influencedto_filename




