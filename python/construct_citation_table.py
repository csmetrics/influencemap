import sqlite3
import os, sys
import pandas as pd
from datetime import datetime 
import numpy as np
import pickle
import warnings

#data_dir = '/Users/xlx/Downloads/graph-data'
data_dir = '/home/xlx/d2/MicrosoftAcademicGraph'

paper_db = os.path.join(data_dir, 'Paper.db')

conn = sqlite3.connect(paper_db)
cur = conn.cursor()

load_ref = lambda fn: pd.read_table(fn, header=None, names=['PaperID', 'RefID'])

conf_file = os.path.join(data_dir, 'data_txt', 'Conferences.txt')
conf_df = pd.read_table(conf_file, header=None, names=['ConfID', 'Abbrv', 'FullName'])


## create a new table with 6 columns
"""
paper (id, conf/jnl, year)  ref (id, conf/jnl, year)
"""
# for each conference, 
#for c in conf_list[:1]:
c = sys.argv[1] #conf_list[0]
row = conf_df.loc[conf_df['Abbrv'] == c]
conf_id = list(row['ConfID'])[0]

output_dir = os.path.join(data_dir, 'out', c)

conf_paper_file = os.path.join(output_dir, 'papers.'+ c +'.txt')
df_paper = pd.read_table(conf_paper_file, header=None, 
                         names=['PaperID', 'TitleOrig', 'TitleNorm', 'PubYear', 'PubDate', 
                               'DOI', 'VenueOrig', 'VenueNorm', 'JournalID', 'ConfID', 'PaperRank' ])
df_paper.head()
set_paper = set(df_paper['PaperID'])

citing_file = os.path.join(output_dir, 'citing.'+c+'.txt')
df_citing = load_ref(citing_file)
cited_file = os.path.join(output_dir, 'cited.'+c+'.txt')
df_cited = load_ref(cited_file)
print ("{} conference {}: {} papers ({}-{})".format(datetime.now(), c, df_paper['PaperID'].count(), 
                                               df_paper['PubYear'].min(), df_paper['PubYear'].max()))
print ("\t citing {} papers, cited by {}".format(df_citing['PaperID'].count(), df_cited['PaperID'].count()))

# left joins for both the citing and cited
dfx_citing = df_citing.merge(df_paper[['PaperID', 'PubYear', 'ConfID']], on='PaperID', how='left') 
dfx_citing = dfx_citing.rename(columns = {'PubYear':'PaperPubYear', 'ConfID':"PaperConfID"})
dfx_citing['RefPubYear'] = 1000
dfx_citing['RefVenueID'] = 'AAAAaaaa'

dfx_cited = df_cited.merge(df_paper[['PaperID', 'PubYear', 'ConfID']], 
                           left_on="RefID", right_on='PaperID', how='left') 
dfx_cited.drop('PaperID_y', axis=1, inplace=True)
dfx_cited = dfx_cited.rename(columns = {'PubYear':'RefPubYear', 'ConfID':"RefConfID", "PaperID_x":"PaperID"})
dfx_cited['PaperPubYear'] = 1000
dfx_cited['PaperVenueID'] = 'AAAAaaaa'


# go over the citing db
cnt = 0

for idx, row in dfx_citing.iterrows():
    cur.execute('SELECT * FROM paper_pruned WHERE id=?', (row['RefID'], ) )
    s = cur.fetchone() 
    #dfx_citing['RefPubYear'][idx] = s[1]
    #dfx_citing['RefVenueID'][idx] = s[2]
    dfx_citing.loc[idx,'RefPubYear'] = s[1]
    dfx_citing.loc[idx,'RefVenueID'] = s[2]
    cnt += 1
    if cnt % 1000 == 0 : # 2000000
        print('{} {:6.0f} / {:6.0f} records'.format(
                datetime.now(), cnt, df_citing['PaperID'].count() ) )
    if cnt >= 1e9: #1e9:
        break

print('{} {:6.0f} / {:6.0f} records. Done.\n\n'.format(
                datetime.now(), cnt, df_citing['PaperID'].count() ) )  


# go over the cited db
cnt = 0

for idx, row in dfx_cited.iterrows():
    cur.execute('SELECT * FROM paper_pruned WHERE id=?', (row['PaperID'], ) )
    s = cur.fetchone() 
    #dfx_cited['PaperPubYear'][idx] = s[1]
    #dfx_cited['PaperVenueID'][idx] = s[2]
    dfx_cited.loc[idx,'PaperPubYear'] = s[1]
    dfx_cited.loc[idx,'PaperVenueID'] = s[2]

    cnt += 1
    if cnt % 1000 == 0 : # 2000000
        print('{} {:6.0f} / {:6.0f} records'.format(
                datetime.now(), cnt, dfx_cited['PaperID'].count() ) )
    if cnt >= 1e9: #1e9:
        break

print('{} {:6.0f} / {:6.0f} records. Done.\n\n'.format(
                datetime.now(), cnt, dfx_cited['PaperID'].count() ) )   

pickle.dump({"name":c, 'citing':dfx_citing, "cited":dfx_cited, "paper":df_paper}, 
           open(os.path.join(output_dir, 'cite_records.'+c+".pkl"), 'wb') ) 

print("saved to " + os.path.join(output_dir, 'cite_records.'+c+".pkl"))
