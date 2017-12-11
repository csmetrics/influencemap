import sqlite3 as sql
import os
import sys
from datetime import datetime
from extractPubModule import name_to_papers
from export_citations_author import construct_cite_db

CHUNK_SIZE = 999

def gen_chunk(rlist):
    chunk = []
    for i, line in enumerate(rlist):
        if (i % CHUNK_SIZE == 0 and i > 0):
            yield chunk
            del chunk[:]
        chunk.append(line)
    yield(chunk)

def do_insert(cur, tname, chunk):
    ins_string = ','.join(['(?)'] * len(chunk))
    cur.execute('INSERT INTO {} VALUES {};'.format(tname, ins_string), chunk)

def cite_table(cur, tname, rlist):
    for chunk in gen_chunk(rlist):
        cur.execute('BEGIN TRANSACTION')

        do_insert(cur, tname, chunk)

        cur.execute('COMMIT')
    

# set database location
#data_dir = "/localdata/u5798145/influencemap"
data_dir = "/localdata/u5642715/influenceMapOut"
db_name = "paper.db"
db_path = os.path.join(data_dir,db_name)
#dir_out = "/localdata/u5798145/influencemap/out"
dir_out = "/localdata/u5642715/influenceMapOut/out"

if not os.path.exists(dir_out):
    os.makedirs(dir_out)

# get name of interest
# author_names = sys.argv[1:]
name = sys.argv[1]
citedDictionary = {}
citingDictionary = {}

# open database connection
conn = sql.connect(db_path)
cur = conn.cursor()
# print("{} input query: {}. Connected to {}".format(datetime.now(), author_names, db_path))

# drop existing any remaining temporary tables
table_names = ["authIDs", "publishedPapers", "citedPapers","citingPapers","reducedPAA",
				"citedPapersAuthors", "citedPaperWeights", "citingPaperWeights", "citingPapersAuthors", "citedAuthorIDs", "citingAuthorIDs"]

for table in table_names:
	print("{} dropping {}".format(datetime.now(), table))
	q = "DROP TABLE IF EXISTS {}".format(table)
	cur.execute(q)

associated_papers = name_to_papers(name)
citing_records, cited_records = construct_cite_db(name, associated_papers)

cur.execute("CREATE TABLE citedPapers (paperID text);")
cur.execute("CREATE TABLE citingPapers (paperID text);")

cite_table(cur, 'citedPapers', cited_records)
cite_table(cur, 'citingPapers', citing_records)

# print(len(citing_records))
# print(len(cited_records))
# 
# for paper_id in citing_records:
#     cur.execute('INSERT INTO citingPapers VALUES (?);', (paper_id,))
# 
# for paper_id in cited_records:
#     cur.execute('INSERT INTO citedPapers VALUES (?);', (paper_id,))

# create reduced database
cur.execute("CREATE TABLE reducedPAA AS SELECT * FROM PAA WHERE paperID IN (SELECT paperID FROM citedPapers UNION SELECT paperID FROM citingPapers)")

# get cited author scores
print("{} connecting papers cited by {} to their respective authors".format(datetime.now(), name))
cur.execute("CREATE TABLE citedPapersAuthors AS SELECT paperID, authorID FROM reducedPAA WHERE paperID IN citedPapers")
print("{} weighting papers cited by {}".format(datetime.now(), name))
cur.execute("CREATE TABLE citedAuthorIDs AS SELECT * FROM authors WHERE authorID IN (SELECT authorID FROM citedPapersAuthors)")
cur.execute("CREATE TABLE citedPaperWeights AS SELECT paperID, (CAST(1 AS float) / CAST(COUNT(authorID) AS float)) AS weightPerAuthor FROM citedPapersAuthors GROUP BY paperID")
print("{} summing weighted scores for authors cited  by {}".format(datetime.now(), name))
cur.execute("SELECT authorName, weightedScore FROM (citedAuthorIDs INNER JOIN (SELECT authorID, CAST(SUM(weightPerAuthor) as float) AS weightedScore  FROM (citedPapersAuthors INNER JOIN citedPaperWeights) GROUP BY authorID) AS authorWeights ON citedAuthorIDs.authorID =authorWeights.authorID)")

print("{} dropping citedPapers and citedPaperWeights tables".format(datetime.now()))

for row in cur.fetchall():
	citedDictionary[row[0]] = row[1]

# get citing author scores
print("{} connecting papers cited by {} to their respective authors".format(datetime.now(), name))
cur.execute("CREATE TABLE citingPapersAuthors AS SELECT paperID, authorID FROM reducedPAA WHERE paperID IN citingPapers")
cur.execute("CREATE TABLE citingAuthorIDs AS SELECT * FROM authors WHERE authorID IN (SELECT authorID FROM citingPapersAuthors)")
print("{} weighting papers that cite {}".format(datetime.now(), name))
cur.execute("CREATE TABLE citingPaperWeights AS SELECT paperID, (CAST(1 AS float) / CAST(COUNT(authorID) AS float)) AS weightPerAuthor FROM citingPapersAuthors GROUP BY paperID")
print("{} summing weighted scores for authors that cite {}".format(datetime.now(), name))
cur.execute("SELECT authorName, weightedScore FROM (citingAuthorIDs INNER JOIN (SELECT authorID, CAST(SUM(weightPerAuthor) as float) AS weightedScore  FROM (citingPapersAuthors INNER JOIN citingPaperWeights) GROUP BY authorID) AS authorWeights ON citingAuthorIDs.authorID =authorWeights.authorID)")


print("{} dropping citingPapers, citingPaperWeights and publishedPapers tables".format(datetime.now()))

for row in cur.fetchall():
	citingDictionary[row[0]] = row[1]

for table in table_names:
	print("{} dropping {}".format(datetime.now(), table))
	q = "DROP TABLE IF EXISTS {}".format(table)
	cur.execute(q)

with open(os.path.join(dir_out, 'authors_cited.txt'), 'w') as fh:
	for key in citedDictionary.keys():
		fh.write("{}\t{}\n".format(key, citedDictionary[key]))

with open(os.path.join(dir_out, 'authors_citing.txt'), 'w') as fh:
	for key in citingDictionary.keys():
		fh.write("{}\t{}\n".format(key, citingDictionary[key]))

# close database connection
print("closing connection to database")
cur.close()
conn.close()

