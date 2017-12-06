import sqlite3
import os, sys
import pandas as pd
from datetime import datetime 
import subprocess

# Input data directory
data_dir = '/mnt/data/MicrosoftAcademicGraph'

# Output data directory
out_dir = '/localdata/u5642715/influenceMapOut'

# database output directory
# db_dir = '/localdata/common'
db_dir = '/localdata/u5642715/influenceMapOut'

# Limit number of query
#batch_size = 800 # MAX=999
batch_size = int(sys.argv[2])

# Need a function which will give a list of papers associated to something
def construct_cite_db(idsearch, paperlist):
    db_path = os.path.join(out_dir, 'paper_ref.db')
    # db_cited = os.path.join(out_dir, idsearch, 'cited.db')
    # db_citing = os.path.join(out_dir, idsearch, 'citing.db')

    cited_records = list()
    citing_records = list()
    # paper_string = ",".join(['"' + paper + '"' for paper in paperlist])
    paper_chunks = [paperlist[x:x+batch_size] for x in range(0, len(paperlist), batch_size)]

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    total_prog = 0
    total = len(paperlist)

    # Gets the paper references the idsearch has referenced (their paper to other papers)
    print('\n---\n{} starting query\n---'.format(datetime.now()))
    for chunk in paper_chunks:
        print('{} start query of paper chunk of size {}'.format(datetime.now(), len(chunk)))
        citing_query = 'SELECT * FROM paper_ref WHERE paper_id IN ({})'.format(','.join(['?'] * len(chunk)))
        cited_query = 'SELECT * FROM paper_ref WHERE paper_ref_id IN ({})'.format(','.join(['?'] * len(chunk)))
        
        
        print('{} citing query'.format(datetime.now()))
        cur.execute(citing_query, chunk)
        citing_records += cur.fetchall()

        print('{} cited query'.format(datetime.now()))
        cur.execute(cited_query, chunk)
        cited_records += cur.fetchall()

        total_prog += len(chunk)
        print('{} finish query of paper chunk, total prog {:.2f}%'.format(datetime.now(), total_prog/total * 100))

    print('---\n{} end query\n---\n'.format(datetime.now()))

    # Output to a file
    citing_file = os.path.join(output_dir, 'citing.'+idsearch+'.txt')
    with open(citing_file, 'wt') as fh:
        fh.write('\n'.join(['\t'.join(s) for s in citing_records] ))

    cited_file = os.path.join(output_dir, 'cited.'+idsearch+'.txt')
    with open(cited_file, 'wt') as fh:
        fh.write('\n'.join(['\t'.join(s) for s in cited_records] ))

    print('saved to {} and {}'.format(citing_file, cited_file))

# OLD GREP
conf_file = os.path.join(data_dir, 'data_txt', 'Conferences.txt')
conf_df = pd.read_table(conf_file, header=None, names=['ConfID', 'Abbrv', 'FullName'])

c = sys.argv[1]
output_dir = os.path.join(out_dir, c)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

row = conf_df.loc[conf_df['Abbrv'] == c]
conf_id = list(row['ConfID'])[0]
#conf_id = '43AA5802' # "43AA5802	MM	ACM Multimedia"
conf_paper_file = os.path.join(output_dir, 'papers.'+ c +'.txt')
#print( conf_id)
#print(conf_paper_file)

if not os.path.exists(conf_paper_file):
    paper_file = os.path.join(data_dir, 'data_txt', 'Papers.txt')
    cmd = "grep " + conf_id +' '+ paper_file + ' > ' + conf_paper_file
    print("{} {}".format(datetime.now(), cmd) )
    os.system(cmd)

df_paper = pd.read_table(conf_paper_file, header=None, 
                         names=['PaperID', 'TitleOrig', 'TitleNorm', 'PubYear', 'PubDate', 
                               'DOI', 'VenueOrig', 'VenueNorm', 'JournalID', 'ConfID', 'PaperRank' ],
                         dtype={'PaperID': str})
df_paper.head()
set_paper = list(df_paper['PaperID'])

#print(set_paper[0])

construct_cite_db(c, set_paper)
