import sqlite3
import os
from datetime import datetime 
import construct_db_config as cfg

# Input data directory
data_dir = cfg.data_dir

# database path
db_path = cfg.db_path

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Join the two constructed tables to make required paper_info table
print('{} start joining papers and paa by paper_id'.format(datetime.now()))
cur.execute('CREATE TABLE paper_info AS SELECT a.paper_id, auth_id, conf_id, affi_id FROM papers a INNER JOIN paa b ON a.paper_id = b.paper_id;')
print('{} finish joining papers and paa by paper_id'.format(datetime.now()))

# Save
conn.commit()
conn.close()
