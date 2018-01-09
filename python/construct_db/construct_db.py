import sqlite3
import os
from datetime import datetime 
from construct_db_func import build_coltype, construct_table, import_to_table, create_index
from construct_db_authname import construct_authname
from construct_db_confname import construct_confname
from construct_db_affiname import construct_affiname
from construct_db_journname import construct_journname
from construct_db_ref import construct_ref
from construct_db_info import construct_paper_info
import construct_db_config as cfg

# Input data directory
data_dir = cfg.data_dir

# database path
db_path = cfg.db_path

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Pragmas to go fast
#cur.execute('PRAGMA journal_mode = OFF')
cur.execute('PRAGMA cache_size = 1000000000')
cur.execute('PRAGMA page_size = 65536')
#cur.execute('PRAGMA synchronous = OFF')
#cur.execute('PRAGMA journal_mode = MEMORY')

construct_confname()
construct_affiname()
construct_authname()
construct_journname()

construct_paper_info()
construct_ref()

# Save
conn.commit()
conn.close()
