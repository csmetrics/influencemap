import sqlite3
import os
import csv
from datetime import datetime 

"""
scheme as a list of strings in order

will delete and remake the specified table if it already exists
"""
def construct_table(conn, name, scheme, override=False):
    try:
        cur = conn.cursor()

        # check if override option is True
        if override:
            print('{} removing table {}'.format(datetime.now(), name))
            cur.execute('DROP TABLE IF EXISTS {};'.format(name))
            print('{} removed table {}'.format(datetime.now(), name))

        print('{} creating table {}'.format(datetime.now(), name))
        cur.execute('CREATE TABLE IF NOT EXISTS {} ({});'.format(name, ",".join(scheme)))
        print('{} created table {}'.format(datetime.now(), name))
    except Error as e:
        print(e)

def remove_outer_quotes(string):
    if string.startswith in quotes and stringendswith in quotes and string.startswith == stringendswith:
        return string[1:-1]
    return string

"""
Imports data from f into the table given by name

dataidx is a list of int which specify to columns in the data which correspond
to colname in order. First column is col 0
"""
def import_to_table(conn, name, f, colname, dataidx, delimitor='\t', rmquotes=False):
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='{}'".format(name))
        if not cur.fetchone:
            raise Exception("Table {} does not exist".format(name))

        # Import table data from file f
        print("{} starting reading data from {}".format(datetime.now(), f))
        with open(f) as data:
            line = data.readline()
            cnt = 0
            while line:
                cnt += 1
                # reorder file data with respect to dataidx
                vals = [line.strip().split(delimitor)[i] for i in dataidx]

                # remove quotes if option
                if rmquotes:
                    vals = map(remove_outer_quotes, vals)

                cur.execute('INSERT INTO {} ({}) VALUES (?, ?);'.format(name, ",".join(colname)), vals)
                if cnt%1e7 == 0:
                    print('{} {:9.0f} lines of data imported into {}'.format(datetime.now(), cnt, name))
                line = data.readline()

            print('{} finished importing {:9.0f} lines of data {}'.format(datetime.now(), cnt, name))
    except Error as e:
        print(e)

"""
EXAMPLE

# Input data directory
data_dir = '/mnt/data/MicrosoftAcademicGraph'

# Output data directory
out_dir = '/localdata/u5642715/influenceMapOut'

ref_db_path = os.path.join(out_dir, 'paper_ref_test.db')

conn = sqlite3.connect(ref_db_path)
cur = conn.cursor()
filepath = os.path.join(data_dir, 'data_txt/PaperReferences.txt')

construct_table(conn, "test", ["a1", "b2"])
import_to_table(conn, "test", filepath, ["a1", "b2"], [1, 0])

conn.commit()
conn.close()
"""
