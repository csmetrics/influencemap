import sqlite3
import os
from datetime import datetime 
from construct_db_func import build_coltype, construct_table, import_to_table, create_index
from construct_db_papers import construct_papers
from construct_db_paa import construct_paa
from construct_db_authname import construct_authname
from construct_db_confname import construct_confname
from construct_db_affiname import construct_affiname
import construct_db_config as cfg

# Input data directory
data_dir = cfg.data_dir

# database path
db_path = cfg.db_path

conn = sqlite3.connect(db_path)
cur = conn.cursor()

construct_confname()
construct_affiname()
construct_authname()

construct_papers()
construct_paa()

# Save
conn.commit()
conn.close()
