import sqlite3
import math
import os
import csv
from datetime import datetime 
from sqlite3 import Error

chunk_size = 1e7

"""
scheme as a list of strings in order

will delete and remake the specified table if it already exists
"""
def construct_table(conn, name, scheme, override=False, primary=[]):
    try:
        cur = conn.cursor()

        # check if override option is True
        if override:
            print('{} removing table {}'.format(datetime.now(), name))
            cur.execute('DROP TABLE IF EXISTS {};'.format(name))
            print('{} removed table {}'.format(datetime.now(), name))

        if primary:
            scheme.append('PRIMARY KEY ({})'.format(",".join(primary)))

        print('{} creating table {}'.format(datetime.now(), name))
        cur.execute('CREATE TABLE IF NOT EXISTS {} ({});'.format(name, ",".join(scheme)))
        print('{} created table {}'.format(datetime.now(), name))
    except Error as e:
        print(e)

def remove_outer_quotes(string):
    if string.startswith in quotes and stringendswith in quotes and string.startswith == stringendswith:
        return string[1:-1]
    return string

def gen_chunks(reader):
    chunk = []
    for i, line in enumerate(reader):
        if (i % chunk_size == 0 and i > 0):
            yield chunk
            del chunk[:]
        chunk.append(line)
    yield(chunk)

"""
Imports data from f into the table given by name

dataidx is a list of int which specify to columns in the data which correspond
to colname in order. First column is col 0
"""
def import_to_table(conn, name, f, colname, dataidx, delim='\t', rmquotes=False, fmap=id):
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='{}'".format(name))
        if not cur.fetchone:
            raise Exception("Table {} does not exist".format(name))

        # Import table data from file f
        print("{} starting reading data from {}".format(datetime.now(), f))
        data = csv.reader(open(f, 'r'), delimiter=delim)
        print("{} finish reading data from {}".format(datetime.now(), f))

        chunk_count = 0
        cnt = 0

        for chunk in gen_chunks(data):
            chunk_count += 1

            print("{} begin preprocessing for chunk {}".format(datetime.now(), chunk_count))

            if rmquotes:
                chunk = list(map(lambda line : list(map(remove_outer_quotes, line)), chunk))

            chunk = list(map(lambda line : list(map(fmap, line)), chunk))
            print("{} finish preprocessing for chunk {}".format(datetime.now(), chunk_count))

            print("{} begin transaction for chunk {}".format(datetime.now(), chunk_count))
            cur.execute('BEGIN TRANSACTION')

            for line in chunk:
                cnt += 1

                cur.execute('INSERT INTO {} ({}) VALUES (?, ?);'.format(name, ",".join(colname)), line)
                if cnt%1e7 == 0:
                    print('{} {:9.0f} lines of data imported into {}'.format(datetime.now(), cnt, name))

            cur.execute('COMMIT')
            print("{} finished transaction for chunk {}".format(datetime.now(), chunk_count))

        print('{} finished importing {:9.0f} lines of data {}'.format(datetime.now(), cnt, name))

    except Error as e:
        print(e)
