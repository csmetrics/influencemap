import sqlite3
import os
import csv
from datetime import datetime 
import re
# from construct_db_func import *

# Input data directory
data_dir = '/mnt/data/MicrosoftAcademicGraph'

# database output directory
db_dir = '/localdata/u5798145/influencemap'

db_path = os.path.join(db_dir, 'paper.db')

conn = sqlite3.connect(db_path)
cur = conn.cursor()

print("{}\tconnected to {}.".format(db_path, datetime.now()))

# paper reference information
ref_name = "paperAuthorAffiliations"
ref_colname = ["paperID text", "authorID text", "affiliationID text", "affiliationNameOriginal text", "affiliationName text", "authorSeqNumber text"]
ref_fileidx = range(6)
ref_datapath = os.path.join(data_dir, 'data_txt/PaperAuthorAffiliations.txt')

cur.execute('drop table if exists {}'.format(ref_name))
cur.execute('create table {} ({})'.format(ref_name,", ".join(ref_colname)))

count = 0

for line in open(ref_datapath, 'r'):
    tokens = line.split('\t')
    tokens = ['"{}"'.format(re.sub('[\'\" ]', '', token)) for token in tokens]
    query = "insert into paperAuthorAffiliations (paperID, authorID, affiliationID, affiliationNameOriginal, affiliationName, authorSeqNumber) values ({})".format(",".join([tokens[i] for i in ref_fileidx]))
    cur.execute(query)
    count += 1
    if count % 100000 == 0:
        print("{}\tinserted {} lines into {}".format(datetime.now(), count, ref_name))

# Save
conn.commit()
conn.close()
