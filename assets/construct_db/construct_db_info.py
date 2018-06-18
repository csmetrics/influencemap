import sqlite3
import os
from datetime import datetime 
import construct_db_config as cfg
from construct_db_func import build_coltype, construct_table, create_index

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

    # Construct table
   # construct_table(conn, table_name, table_coltype, override=True)

   # # Count the number of authors per paper
   # print('{} start count authors per paper'.format(datetime.now()))
   # cur.execute('INSERT INTO authcount (paper_id, auth_count) SELECT paper_id, Count(*) FROM paa GROUP BY paper_id;')
   # print('{} finish count authors per paper'.format(datetime.now()))
   # conn.commit()

   # # Index authcount for faster join
   # create_index(conn, table_name, table_col[0])
   # conn.commit()

   # # Join tables together with count
   # print('{} start join paa with authcount'.format(datetime.now()))
   # cur.execute('DROP TABLE IF EXISTS paa_count;')
   # cur.execute('CREATE TABLE paa_count AS SELECT a.paper_id, auth_id, auth_count, affi_id FROM paa a INNER JOIN authcount b ON a.paper_id = b.paper_id;')
   # print('{} finish join paa with authcount'.format(datetime.now()))
   # conn.commit()
   # create_index(conn, 'paa_count', table_col[0])

   # # Join the two constructed tables to make required paper_info table
   # print('{} start joining papers and paa_count by paper_id'.format(datetime.now()))
   # cur.execute('DROP TABLE IF EXISTS paper_info_tmp1;')
   # cur.execute('CREATE TABLE paper_info_tmp1 AS SELECT a.paper_id, pub_year, auth_id, auth_count, conf_id, journ_id, affi_id FROM papers a INNER JOIN paa_count b ON a.paper_id = b.paper_id;')
   # print('{} finish joining papers and paa_count by paper_id'.format(datetime.now()))
   # conn.commit()
   # create_index(conn, 'paper_info_tmp1', 'auth_id')

    # Join the two constructed tables to make required paper_info table
    print('{} start joining for auth names'.format(datetime.now()))
    cur.execute('DROP TABLE IF EXISTS paper_info_tmp2;')
    cur.execute('CREATE TABLE paper_info_tmp2 AS SELECT paper_id, pub_year, a.auth_id, auth_name, auth_count, conf_id, journ_id, affi_id FROM paper_info_tmp1 a LEFT JOIN authname b ON a.auth_id = b.auth_id;')
    cur.execute('DROP TABLE IF EXISTS paper_info_tmp1;')
    print('{} finish joining for auth names'.format(datetime.now()))
    conn.commit()
    create_index(conn, 'paper_info_tmp2', 'conf_id')

    # Join the two constructed tables to make required paper_info table
    print('{} start joining for conf names'.format(datetime.now()))
    cur.execute('DROP TABLE IF EXISTS paper_info_tmp3;')
    cur.execute('CREATE TABLE paper_info_tmp3 AS SELECT paper_id, pub_year, auth_id, auth_name, auth_count, a.conf_id, conf_abv, conf_name, journ_id, affi_id FROM paper_info_tmp2 a LEFT JOIN confname b ON a.conf_id = b.conf_id;')
    cur.execute('DROP TABLE IF EXISTS paper_info_tmp2;')
    print('{} finish joining for conf names'.format(datetime.now()))
    conn.commit()
    create_index(conn, 'paper_info_tmp3', 'journ_id')

    # Join the two constructed tables to make required paper_info table
    print('{} start joining for journ names'.format(datetime.now()))
    cur.execute('DROP TABLE IF EXISTS paper_info_tmp4;')
    cur.execute('CREATE TABLE paper_info_tmp4 AS SELECT paper_id, pub_year, auth_id, auth_name, auth_count, conf_id, conf_abv, conf_name, a.journ_id, journ_name, affi_id FROM paper_info_tmp3 a LEFT JOIN journname b ON a.journ_id = b.journ_id;')
    cur.execute('DROP TABLE IF EXISTS paper_info_tmp3;')
    print('{} finish joining for journ names'.format(datetime.now()))
    conn.commit()
    create_index(conn, 'paper_info_tmp4', 'affi_id')

    # Join the two constructed tables to make required paper_info table
    print('{} start joining for affi names'.format(datetime.now()))
    cur.execute('DROP TABLE IF EXISTS paper_info;')
    cur.execute('CREATE TABLE paper_info AS SELECT paper_id, pub_year, auth_id, auth_name, auth_count, conf_id, conf_abv, conf_name, journ_id, journ_name, a.affi_id, affi_name FROM paper_info_tmp4 a LEFT JOIN affiname b ON a.affi_id = b.affi_id;')
    cur.execute('DROP TABLE IF EXISTS paper_info_tmp3;')
    print('{} finish joining for affi names'.format(datetime.now()))
    conn.commit()

    # Index paper_info wrt paper_id
    create_index(conn, 'paper_info', table_col[0])

    # Save
    conn.commit()
    cur.close()
    conn.close()

if __name__ == '__main__':
    construct_paper_info()
