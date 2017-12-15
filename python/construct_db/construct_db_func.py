import sqlite3
import math
import itertools
import os
import csv
import sys
from datetime import datetime 
from sqlite3 import Error

csv.field_size_limit(sys.maxsize)
chunk_limit = 999
quotes = ['\'', '\"']

def build_coltype(clist, tlist):
    res = list()
    for c, t in zip(clist, tlist):
        res.append(c + ' ' + t)
    return res

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

        cur.close()
    except Error as e:
        print(e)

def gen_chunks(reader, chunk_size, idx):
    chunk = []
    for i, line in enumerate(reader):
        if (i % chunk_size == 0 and i > 0):
            yield chunk
            del chunk[:]
        chunk.append([line[i] for i in idx])
    yield(chunk)

def do_insert(cur, chunk, name, colname):
    num_cols = len(colname)
    vals = list(map(lambda line : '({})'.format(','.join(line)), chunk))
    num_ins = len(vals)
    # ins_string = ','.join(['({})'.format(','.join((['?'] * num_cols)))] * num_ins)
    ins_string = ','.join(['({})'.format(','.join((['?'] * num_cols)))] * num_ins)

    cur.execute('INSERT INTO {} ({}) VALUES {};'.format(name, ",".join(colname), ins_string), list(itertools.chain.from_iterable((chunk))))


"""
Imports data from f into the table given by name

dataidx is a list of int which specify to columns in the data which correspond
to colname in order. First column is col 0
"""
def import_to_table(conn, name, f, colname, dataidx, delim='\t', fmap=None, transaction=True):
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='{}'".format(name))
        if not cur.fetchone:
            raise Exception("Table {} does not exist".format(name))

        # Import table data from file f
        print("{} starting reading data from {}".format(datetime.now(), f))
        data = csv.reader(open(f, 'r'), delimiter=delim)
        print("{} finish reading data from {}".format(datetime.now(), f))
                
        if transaction:
            # chunk + transactions
            chunk_size = math.floor(chunk_limit / len(colname))
            chunk_count = 0
            row_count = 0

            for chunk in gen_chunks(data, chunk_size, dataidx):
                chunk_count += 1
                row_count += len(chunk)

                #print("{} begin preprocessing for chunk {}".format(datetime.now(), chunk_count))

                if fmap:
                    chunk = map(lambda line : list(map(fmap, line)), chunk)

                chunk = list(map(lambda line : list(map(lambda s : str(s), line)), chunk))
                #print("{} finish preprocessing for chunk {}".format(datetime.now(), chunk_count))

                #print("{} begin transaction for chunk {}".format(datetime.now(), chunk_count))
                cur.execute('BEGIN TRANSACTION')

                do_insert(cur, chunk, name, colname)

                cur.execute('COMMIT')
                if chunk_count % 1e4 == 0:
                    print("{} finished transaction for chunk {} with {} rows".format(datetime.now(), chunk_count, row_count))
            print("{} finished transaction for chunk {} with {} rows".format(datetime.now(), chunk_count, row_count))

        else:
            # line by line
            ins_string = '({})'.format(','.join((['?'] * num_cols)))
            row_count = 0

            for line in data:
                row_count += 1
                iline = map(lambda s : str(s), [line[i] for i in idx])
                cur.execute('INSERT INTO {} ({}) VALUES {};'.format(name, ",".join(colname), ins_string), list(iline))
                if line_count % 1e6 == 0:
                    print("{} finished inserting {} rows".format(datetime.now(), row_count))

        cur.close()

    except Error as e:
        print(e)

def create_index(conn, table, col):
    cur = conn.cursor()

    idx_name = 'indx_{}_{}'.format(table, col)
    print('{} indexing {} in {}'.format(datetime.now(), col, table))
    cur.execute('CREATE INDEX {} ON {} ({});'.format(idx_name, table, col))
    print('{} indexed {} in {}'.format(datetime.now(), col, table))

    cur.close()
