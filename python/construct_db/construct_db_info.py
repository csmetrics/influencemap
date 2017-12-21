import sqlite3
import os
from datetime import datetime 
import construct_db_config as cfg
from construct_db_func import build_coltype, construct_table, create_index
from construct_db_papers import construct_papers
from construct_db_paa import construct_paa

# Input data directory
data_dir = cfg.data_dir

# database path
db_path = cfg.db_path


# Create count table
# Table details
table_name = 'authcount'
table_col = ['paper_id', 'auth_count']
table_type = ['text', 'int']
table_coltype = build_coltype(table_col, table_type)

def construct_paper_info():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
# Construct dependent tables construct_papers() construct_paa() 
    # Construct table
    construct_table(conn, table_name, table_coltype, override=True)

    # Count the number of authors per paper
    print('{} start count authors per paper'.format(datetime.now()))
    cur.execute('INSERT INTO authcount (paper_id, auth_count) SELECT paper_id, Count(*) FROM paa GROUP BY paper_id;')
    print('{} finish count authors per paper'.format(datetime.now()))

    # Index authcount for faster join
    create_index(conn, table_name, table_col[0])

    # Join tables together with count
    print('{} start join paa with authcount'.format(datetime.now()))
    cur.execute('DROP TABLE IF EXISTS paa_count;')
    cur.execute('CREATE TABLE paa_count AS SELECT a.paper_id, auth_id, auth_count, affi_id FROM paa a INNER JOIN authcount b ON a.paper_id = b.paper_id;')
    print('{} finish join paa with authcount'.format(datetime.now()))

    # Join the two constructed tables to make required paper_info table
    print('{} start joining papers and paa_count by paper_id'.format(datetime.now()))
    cur.execute('DROP TABLE IF EXISTS paper_info;')
    cur.execute('CREATE TABLE paper_info AS SELECT a.paper_id, auth_id, auth_count, conf_id, journ_id, affi_id FROM papers a INNER JOIN paa_count b ON a.paper_id = b.paper_id;')
    print('{} finish joining papers and paa_count by paper_id'.format(datetime.now()))

    # Index paper_info wrt paper_id
    create_index(conn, 'paper_info', table_col[0])

    # Save
    conn.commit()
    cur.close()
    conn.close()

if __name__ == '__main__':
    construct_paper_info()
