import sqlite3
import os
import csv
from datetime import datetime 
import construct_db_func

# Input data directory
data_dir = '/mnt/data/MicrosoftAcademicGraph'

# database output directory
db_dir = '/localdata/common'

db_path = os.path.join(out_dir, 'paper_ref.db')

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# paper reference information
ref_name = "paper_ref"
ref_colname = ["paper_id text", "paper_ref_id text"]
ref_fileidx = [0, 1]
ref_datapath = os.path.join(data_dir, 'data_txt/PaperReferences.txt')

# Create table
construct_table(conn, ref_name, ref_colname)

# Import table data from data
import_to_table(conn, ref_name, ref_datapath, ref_colname, ref_fileidx)

# Index data
print('{} indexing paper_id in paper_ref'.format(datetime.now()))
cur.execute('CREATE INDEX idx_paper_id ON paper_ref (paper_id);')
print('{} indexed paper_id in paper_ref'.format(datetime.now()))

print('{} indexing paper_ref_id in paper_ref'.format(datetime.now()))
cur.execute('CREATE INDEX idx_paper_ref_id ON paper_ref (paper_ref_id);')
print('{} indexed paper_ref_id in paper_ref'.format(datetime.now()))

# Set sync OFF
cur.execute('PRAGMA synchronous=OFF';)

# Save
conn.commit()
conn.close()
