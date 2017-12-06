import sqlite3
import os
import csv
from datetime import datetime 
import construct_db_func

# Input data directory
data_dir = '/mnt/data/MicrosoftAcademicGraph'

# Output data directory
out_dir = '/localdata/u5642715/influenceMapOut'

db_path = os.path.join(out_dir, 'paper.db')

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# paper reference information
ref_name = "paper_ref"
ref_colname = ["paper_id text", "paper_ref_id text"]
ref_fileidx = [0, 1]
ref_datapath = os.path.join(out_dir, 'paper_ref_test.db')

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

# Save
conn.commit()
conn.close()
