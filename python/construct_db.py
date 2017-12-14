import sqlite3
import os
import csv
from datetime import datetime 
from construct_db_func import construct_table, import_to_table

# Input data directory
data_dir = '/mnt/data/MicrosoftAcademicGraph/data_txt'

# database output directory
#db_dir = '/localdata/common'
db_dir = '/home/u5642715/data_loc/influenceMapOut'

db_path = os.path.join(db_dir, 'paper_info.db')

conn = sqlite3.connect(db_path)
cur = conn.cursor()

def build_coltype(clist, tlist):
    res = list()
    for c, t in zip(clist, tlist):
        res.append(c + ' ' + t)
    return res

table_name = ['papers', 'paa']
table_col = [['paper_id', 'conf_id'], ['paper_id', 'author_id', 'inst_id']]
table_type = [['text', 'text'], ['text', 'text', 'text']]
table_coltype = map(lambda t : build_coltype(t[0], t[1]), zip(table_col, table_type))

# construct initial tables straight from data
for name, coltype in zip(table_name, table_coltype):
    construct_table(conn, name, coltype, override=True)

data_files = ['Papers.txt', 'PaperAuthorAffiliations.txt']
data_ids = [[0, 9], [0, 1, 2]]
data_paths = map(lambda f : os.path.join(data_dir, f), data_files)

for name, fpath, col, ids in zip(table_name, data_paths, table_col, data_ids):
    import_to_table(conn, name, fpath, col, ids)

# Index the tables by paperid
print('{} indexing paper_id in papers'.format(datetime.now()))
cur.execute('CREATE INDEX idx_paper_id ON papers (paper_id);')
print('{} indexed paper_id in papers'.format(datetime.now()))

print('{} indexing paper_id in paa'.format(datetime.now()))
cur.execute('CREATE INDEX idx_paper_id ON paa (paper_id);')
print('{} indexed paper_id in paa'.format(datetime.now()))

# Join the two constructed tables to make required paper_info table
print('{} start joining papers and paa by paper_id'.format(datetime.now()))
cur.execute('CREATE paper_info AS SELECT a.paper_id, author_id, conf_id, inst_id FROM papers a INNER JOIN paa b ON a.paper_id = b.paper_id;')
print('{} finish joining papers and paa by paper_id'.format(datetime.now()))
     
# Save
conn.commit()
conn.close()
