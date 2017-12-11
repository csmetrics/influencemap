import sqlite3
import os
import csv
from datetime import datetime 
from construct_db_func import construct_table, import_to_table

# Input data directory
data_dir = '/mnt/data/MicrosoftAcademicGraph'

# database output directory
#db_dir = '/localdata/common'
db_dir = '/home/u5642715/data_loc/influenceMapOut'

db_path = os.path.join(db_dir, 'paper_ref_integer.db')

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# paper reference information
ref_name = "paper_ref"
ref_colnametype = ["paper_id INTEGER", "paper_ref_id INTEGER"]
ref_fileidx = [0, 1]
ref_colname = ["paper_id", "paper_ref_id"]
ref_datapath = os.path.join(data_dir, 'data_txt/PaperReferences.txt')

# Set sync OFF
cur.execute('PRAGMA synchronous=OFF;')

# Create table
construct_table(conn, ref_name, ref_colnametype, override=True, primary=ref_colname)

# Import table data from data
convert_to_int = lambda string : int(string, 16)
import_to_table(conn, ref_name, ref_datapath, ref_colname, ref_fileidx, fmap=convert_to_int)

# Index data
print('{} indexing paper_id in paper_ref'.format(datetime.now()))
cur.execute('CREATE INDEX idx_paper_id ON paper_ref (paper_id);')
print('{} indexed paper_id in paper_ref'.format(datetime.now()))

print('{} indexing paper_ref_id in paper_ref'.format(datetime.now()))
cur.execute('CREATE INDEX idx_paper_ref_id ON paper_ref (paper_ref_id);')
print('{} indexed paper_ref_id in paper_ref'.format(datetime.now()))

# Other pragmas
cur.execute('PRAGMA count_changes=OFF;')


# Save
conn.commit()
conn.close()
