import sqlite3, os
from datetime import datetime
from construct_db_func import build_coltype, construct_table, import_to_table

# Input data directory
data_dir = '/mnt/data/MicrosoftAcademicGraph/data_txt'

# database output directory
db_dir = '/home/u5642715/data_loc/influenceMapOut'

db_path = os.path.join(db_dir, 'paper_info.db')

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Table details
table_name = 'auth_name'
table_col = ['auth_id', 'auth_name']
table_type = ['text', 'text']
table_coltype = build_coltype(table_col, table_type)

# Construct table
construct_table(conn, name, coltype, override=True)

# Data file details
data_file = 'Authors.txt'
data_ids = [0, 1]
data_path = os.path.join(data_dir, data_file)

# Import data to table
import_to_table(conn, name, data_path, table_col, data_ids)

# Index first column
create_index(table_name, table_col[0])
