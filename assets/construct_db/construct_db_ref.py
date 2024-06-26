import sqlite3, os
from datetime import datetime
from construct_db_func import build_coltype, construct_table, import_to_table, create_index
import construct_db_config as cfg
from func import *

# Input data directory
data_dir = cfg.data_dir

# database path
db_path = cfg.db_path

# paper_ref
# Table details
table_name = 'paper_ref'
table_col = ['paper_id', 'paper_ref_id']
table_type = ['text', 'text']
table_coltype = build_coltype(table_col, table_type)

# Data file details
data_file = 'PaperReferences.txt'
data_ids = [0, 1]
data_path = os.path.join(data_dir, data_file)

# ref count
# Table details
rtable_name = 'ref_count'
rtable_col = ['paper_id', 'ref_count']
rtable_type = ['text', 'int']
rtable_coltype = build_coltype(rtable_col, rtable_type)

# combined table
ctable_name = 'paper_ref_count'
ctable_col = ['paper_id', 'paper_ref_id', 'paper_rc']
ctable_type = ['text', 'text', 'int']
ctable_coltype = build_coltype(ctable_col, ctable_type)

def construct_ref():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Construct table
    construct_table(conn, table_name, table_coltype, override=True)

    # Import data to table
    import_to_table(conn, table_name, data_path, table_col, data_ids)

    # Index first column
    create_index(conn, table_name, table_col[0])

    # Construct count table
    construct_table(conn, rtable_name, rtable_coltype, override=True)

    # Cound number of references per paper    
    print('{} start count references per paper'.format(datetime.now()))
    cur.execute('INSERT INTO ref_count (paper_id, ref_count) SELECT paper_id, Count(*) FROM paper_ref GROUP BY paper_id;')
    conn.commit()
    print('{} finish count references per paper'.format(datetime.now()))

    # Index ref_count for faster join
    create_index(conn, rtable_name, rtable_col[0])

    # Join tables together with count
    # construct combined table
    construct_table(conn, ctable_name, ctable_coltype, override=True)

    print('{} start join paper_ref with authcount'.format(datetime.now()))
    cur.execute('INSERT INTO paper_ref_count (paper_id, paper_ref_id, paper_rc) SELECT a.paper_id, paper_ref_id, ref_count FROM ref_count a INNER JOIN paper_ref b ON a.paper_id = b.paper_id;')
    conn.commit()
    print('{} finish join paper_ref with authcount'.format(datetime.now()))

    # index final table
    create_index(conn, ctable_name, ctable_col[0])
    create_index(conn, ctable_name, ctable_col[1])

    # Save
    conn.commit()
    cur.close()
    conn.close()

if __name__ == '__main__':
    construct_ref()
