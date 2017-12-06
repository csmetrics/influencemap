import sqlite3
import os
import csv
from datetime import datetime 

# Input data directory
data_dir = '/mnt/data/MicrosoftAcademicGraph'

# Output data directory
out_dir = '/localdata/u5642715/influenceMapOut'

ref_db_path = os.path.join(out_dir, 'paper_ref.db')

conn = sqlite3.connect(ref_db_path)
cur = conn.cursor()

# Create table
print('{} creating table for paper_ref'.format(datetime.now()))
cur.execute('DROP TABLE IF EXISTS paper_ref;')
cur.execute('CREATE TABLE paper_ref (paper_id text, paper_ref_id text);')
print('{} created table for paper_ref'.format(datetime.now()))

# Import table data from data
print('{} importing data into paper_ref'.format(datetime.now()))
with open(os.path.join(data_dir, 'data_txt/PaperReferences.txt')) as data:
    line = data.readline()
    cnt = 0
    while line:
        cnt += 1
        vals = line.strip().split('\t')
        cur.execute('INSERT INTO paper_ref (paper_id, paper_ref_id) VALUES (?, ?);', vals)
        if cnt%1e7 == 0:
            print('{} {:9.0f} lines of data imported into paper_ref'.format(datetime.now(), cnt))
        line = data.readline()

print('{} finished importing {:9.0f} lines of data into paper_ref'.format(datetime.now(), cnt))

# Index data
print('{} indexing paper_id in paper_ref'.format(datetime.now()))
cur.execute('CREATE INDEX idx_paper_id ON paper_ref (paper_id);')
print('{} indexed paper_id in paper_ref'.format(datetime.now()))

print('{} indexing paper_ref_id in paper_ref'.format(datetime.now()))
cur.execute('CREATE INDEX idx_paper_ref_id ON paper_ref (paper_ref_id);')
print('{} indexed paper_ref_id in paper_ref'.format(datetime.now()))

# Save
conn.commit()
conn.close()
