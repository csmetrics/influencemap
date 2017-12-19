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

# Limit number of query
BATCH_SIZE = 999 # MAX=999

# Need a function which will give a list of papers associated to something
def construct_cite_db(idsearch, paperlist):
    db_path = os.path.join(out_dir, 'paper_ref.db')

    papers_citing_me_records = list()
    papers_cited_by_me_records = list()
    paper_chunks = [paperlist[x:x+BATCH_SIZE] for x in range(0, len(paperlist), BATCH_SIZE)]

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    total_prog = 0
    total = len(paperlist)

    # Gets the paper references the idsearch has referenced (their paper to other papers)
    print('\n---\n{} starting query\n---'.format(datetime.now()))
    for chunk in paper_chunks:
        print('{} start query of paper chunk of size {}'.format(datetime.now(), len(chunk)))
        papers_citing_me_q = 'SELECT paper_id FROM paper_ref WHERE paper_ref_id IN ({})'.format(','.join(['?'] * len(chunk)))
        papers_cited_by_me_q = 'SELECT paper_ref_id FROM paper_ref WHERE paper_id IN ({})'.format(','.join(['?'] * len(chunk)))
        
        
        print('{} papers_citing_me'.format(datetime.now()))
        print(chunk)
        cur.execute(papers_citing_me_q, chunk)
        papers_citing_me_records += list(map(lambda t : t[0], cur.fetchall()))

        print('{} papers_cited_by_me_q'.format(datetime.now()))
        cur.execute(papers_cited_by_me_q, chunk)
        papers_cited_by_me_records += list(map(lambda t : t[0], cur.fetchall()))

        total_prog += len(chunk)
        print('{} finish query of paper chunk, total prog {:.2f}%'.format(datetime.now(), total_prog/total * 100))

    print('---\n{} end query\n---\n'.format(datetime.now()))

    cur.close()
    conn.close()

    return papers_citing_me_records, papers_cited_by_me_records

if __name__ == '__main__':
    from extract_papers import name_to_papers

    user_in = sys.argv[1]

    associated_papers = name_to_papers(user_in)

    construct_cite_db(user_in, associated_papers)
