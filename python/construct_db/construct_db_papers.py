import sqlite3, os
from datetime import datetime
from construct_db_func import build_coltype, construct_table, import_to_table
import construct_db_config as cfg

# Input data directory
data_dir = cfg.data_dir

# database output directory
db_dir = cfg.data_dir

db_path = os.path.join(db_dir, 'paper_info.db')

# Table details
table_name = 'papers'
table_col = ['paper_id', 'conf_id']
table_type = ['text', 'text']
table_coltype = build_coltype(table_col, table_type)

# Data file details
data_file = 'Papers.txt'
data_ids = [0, 9]
data_path = os.path.join(data_dir, data_file)

def construct_papers():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Construct table
    construct_table(conn, name, coltype, override=True)

    # Import data to table
    import_to_table(conn, name, data_path, table_col, data_ids)

    # Index first column
    create_index(table_name, table_col[0])
         
    # Save
    conn.commit()
    conn.close()

if __name__ == '__main__':
    construct_papers()
