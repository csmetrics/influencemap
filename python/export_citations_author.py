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
db_dir = '/localdata/common'
# db_dir = '/localdata/u5642715/influenceMapOut'

# Limit number of query
batch_size = 999 # MAX=999
#batch_size = int(sys.argv[2])

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
        citing_query = 'SELECT paper_ref_id FROM paper_ref WHERE paper_ref_id IN ({})'.format(','.join(['?'] * len(chunk)))
        cited_query = 'SELECT paper_id FROM paper_ref WHERE paper_id IN ({})'.format(','.join(['?'] * len(chunk)))
        
        
        print('{} citing query'.format(datetime.now()))
        cur.execute(citing_query, chunk)
        citing_records += list(map(lambda t : t[0], cur.fetchall()))

        print('{} cited query'.format(datetime.now()))
        cur.execute(cited_query, chunk)
        cited_records += list(map(lambda t : t[0], cur.fetchall()))

        total_prog += len(chunk)
        print('{} finish query of paper chunk, total prog {:.2f}%'.format(datetime.now(), total_prog/total * 100))

    print('---\n{} end query\n---\n'.format(datetime.now()))

    cur.close()
    conn.close()

    return citing_records, cited_records

    """
    output_dir = os.path.join(out_dir, idsearch)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Output to a file
    citing_file = os.path.join(output_dir, 'citing.'+idsearch+'.txt')
    with open(citing_file, 'wt') as fh:
        fh.write('\n'.join(['\t'.join(s) for s in citing_records] ))

    cited_file = os.path.join(output_dir, 'cited.'+idsearch+'.txt')
    with open(cited_file, 'wt') as fh:
        fh.write('\n'.join(['\t'.join(s) for s in cited_records] ))

    print('saved to {} and {}'.format(citing_file, cited_file))
    """

if __name__ == '__main__':
    from extractPub import name_to_papers

    user_in = sys.argv[1]

    associated_papers = name_to_papers(user_in)

    construct_cite_db(user_in, associated_papers)
