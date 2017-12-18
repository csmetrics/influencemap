import sqlite3
import os
import sys
from datetime import datetime
from extract_papers import name_to_papers
from export_citations_author import construct_cite_db

# Limit number of query
BATCH_SIZE = 999 # MAX=999

# database location
db_dir = "/localdata/u5642715/influenceMapOut"

# output directory
dir_out = "/localdata/u5642715/influenceMapOut/out"

# for authors
def gen_score(conn, plist):
    res = dict()
    id_to_name = dict()

    # split papers into chunks
    total_prog = 0
    total = len(plist)
    paper_chunks = [plist[x:x+BATCH_SIZE] for x in range(0, total, BATCH_SIZE)]

    cur = conn.cursor()

    for chunk in paper_chunks:
        # query plan for this
        output_scheme = ",".join(['auth_id', 'auth_count'])
        targets = ','.join(['?'] * len(chunk))
        query = 'SELECT {} FROM paper_info WHERE paper_id IN ({})'.format(output_scheme, targets)

        cur.execute(query, chunk)

        # iterate through query results
        for line in cur.fetchall():
            auth_id, auth_count = line

            # check ids_to_name dictionary
            try:
                auth_name = id_to_name[auth_id]
            except KeyError:
                key_scheme = 'auth_id'
                id_query = 'SELECT * FROM authname WHERE {} = ? LIMIT 1'.format(key_scheme)
                
                cur.execute(id_query, (auth_id, ))
                _, name = cur.fetchone()
                auth_name = ' '.join(name.split())

                id_to_name[auth_id] = auth_name

            # Add to score
            try:
                res[auth_name] += 1 / auth_count
            except KeyError:
                res[auth_name] = 1 / auth_count

        # progression
        total_prog += len(chunk)
        print('{} finish query of paper chunk, total prog {:.2f}%'.format(datetime.now(), total_prog/total * 100))

    cur.close()

    # return dict results
    return res

'''
def gen_citing_score(cur, emap, plist):
    res = {}

    # split papers into chunks
    paper_chunks = [plist[x:x+BATCH_SIZE] for x in range(0, len(plist), BATCH_SIZE)]
    total_prog = 0
    total = len(paperlist)

    # query papers per chunk
    for chunk in paper_chunks:
        # paperid | authorid | authorname | numauthors
        query = 'SELECT * FROM PAA WHERE paper_id IN ({})'.format(','.join(['?'] * len(chunk)))

        print('{} start query of paper chunk of size {}'.format(datetime.now(), len(chunk)))

        cur.execute(query, chunk)

        # turn query results into scores per author id
        for paper_id, author_id, author_name, score in cur.fetchall():
            res[author_name] += score
        total_prog += len(chunk)

        print('{} finish query of paper chunk, total prog {:.2f}%'.format(datetime.now(), total_prog/total * 100))

    return res
'''

if __name__ == "__main__":

    # input
    name = sys.argv[1]

    # get paper ids associated with input name
    print('{} start get associated papers to input name {}'.format(datetime.now(), name))
    associated_papers = name_to_papers(name)
    print('{} finish get associated papers to input name {}'.format(datetime.now(), name))

    # filter ref papers
    print('{} start filter paper references'.format(datetime.now()))
    citing_papers, cited_papers = construct_cite_db(name, associated_papers)
    print('{} finish filter paper references'.format(datetime.now()))

    db_path = os.path.join(db_dir, 'paper_info.db')
    conn = sqlite3.connect(db_path)

    # Generate associated author scores for citing and cited
    citing_records = gen_score(conn, citing_papers)
    cited_records = gen_score(conn, cited_papers)

    # Print to file (Do we really need this?
    with open(os.path.join(dir_out, 'authors_citing.txt'), 'w') as fh:
        for key in citing_records.keys():
            fh.write("{}\t{}\n".format(key, citing_records[key]))

    with open(os.path.join(dir_out, 'authors_cited.txt'), 'w') as fh:
        for key in cited_records.keys():
            fh.write("{}\t{}\n".format(key, cited_records[key]))

    conn.close()
