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
ctable_col = ['paper_id', 'paper_ref_id', 'paper_rc', 'paper_ref_rc']
ctable_type = ['text', 'text', 'int', 'int']
ctable_coltype = build_coltype(ctable_col, ctable_type)

def num_refs(conn, paper_id, num_refs_dict):
    query = 'SELECT Count(paper_ref_id) FROM paper_ref WHERE paper_id WHERE paper_id = ?'
    func = lambda f : f[0][0]
    return try_get(conn, paper_id, num_refs_dict, func=func)

def is_selfcite(conn, paper_id, paper_ref_id, auth_dict):
    sc_query = 'SELECT author_id FROM paper_info WHERE paper_id = ?'.format(key)
    func = lambda f : set(map(lambda r : r[0], f))

    my_auth = try_get(conn, paper_id, auth_dict, sc_query, func=func)
                    
    their_auth = try_get(conn, paper_auth, auth_dict, sc_query, func=func)

    return not my_auth.isdisjoint(their_auth)

def construct_ref():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Construct table
    construct_table(conn, table_name, table_coltype, override=True)

    # Import data to table
    import_to_table(conn, table_name, data_path, table_col, data_ids)

    # Index both column
    create_index(conn, table_name, table_col[0])
    create_index(conn, table_name, table_col[1])

    # Construct count table
    construct_table(conn, rtable_name, rtable_coltype, override=True)

    # Cound number of references per paper    
    print('{} start count references per paper'.format(datetime.now()))
    cur.execute('INSERT INTO ref_count (paper_id, ref_count) SELECT paper_id, Count(*) FROM paper_ref GROUP BY paper_id;')
    print('{} finish count references per paper'.format(datetime.now()))

    # Index ref_count for faster join
    create_index(conn, rtable_name, rtable_col[0])

    # Join tables together with count
    print('{} start join paper_ref with authcount'.format(datetime.now()))
    cur.execute('DROP TABLE IF EXISTS paper_ref_tmp;')
    cur.execute('CREATE TABLE paper_ref_tmp AS SELECT a.paper_id, paper_ref_id, ref_count FROM ref_count a INNER JOIN paper_ref b ON a.paper_id = b.paper_id;')

    # construct combined table
    construct_table(conn, ctable_name, ctable_coltype, override=True)

    cur.execute('INSERT INTO paper_ref_count (paper_id, paper_ref_id, paper_rc, paper_ref_rc) SELECT b.paper_id, b.paper_ref_id, b.ref_count, a.ref_count FROM paper_ref_tmp b INNER JOIN ref_count a ON a.paper_id = b.paper_ref_id;')
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
