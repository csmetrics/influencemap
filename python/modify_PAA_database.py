'''
created 13/12/17 by Ben Readshaw
purpose: fall back script to add paper weight and author name to paper author affiliation table
'''

import sqlite3, os
from datetime import datetime

# define data location
db_dir = '/localdata/u5798145/influencemap'
db_name = 'paper.db'
db_path = os.path.join(data_dir, db_name)
txt_dir = '/mnt/data/MicrosoftAcademicGraph/data_txt'
paa_txt_name = 'PaperAuthorAffiliations.txt'
auth_txt_name = 'Authors.txt'
paa_path = os.path.join(txt_dir, paa_txt_name)
auth_path = os.path.join(txt_dir, auth_txt_name)

# define table and column names
paa_table = 'PAA'
author_table = 'authors'
pid_column = 'paperID'
aid_column = 'authorID'
author_name_column = 'authorName'
new_weight_column = 'weight'

# connect to database
print("{}\tconnecting to database".format(datetime.now().time()))
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# add new columns
print("{}\taltering table".format(datetime.now().time()))
cur.execute('alter table {} add column {} text'.format(paa_table, new_weight_column))
cur.execute('alter table {} add column {} text'.format(paa_table, author_name_column))

# get paper weights
print("{}\tgetting paper weights".format(datetime.now().time()))
paperWeights = dict()
for line in open(paa_path):
	tokens = line.split('\t')
	pid = tokens[0]
	aid_paa = tokens[1]
	try:
		paperWeights[pid].add(aid_paa)
	except:
		paperWeights[pid] = set(aid_paa)

# get author names
print("{}\tgetting author names".format(datetime.now().time()))
authorNames = dict()
for line in open(auth_path):
	tokens = line.split('\t')
	aid_auth = tokens[0]
	authName = tokens[1]
	try:
		paperWeights[aid_auth].add(authName)
	except:
		paperWeights[aid_auth] = set(authName)

# add values to new columns
print("{}\tgettingpaper weights".format(datetime.now().time()))
count = 0
for line in open(paa_path):
	tokens = line.split('\t')
	pid = tokens[0]
	aid_paa = tokens[1]
	weight = 1 / len(paperWeights[pid])
	name = authorNames[aid_paa]	
	cur.execute('insert into {} ({}, {}) values ({}, {})'.format(paa_table, new_weight_column, author_name_column, weight, name))
	count += 1
	if count % 1000000 == 0:
		print("{}\tinserted new values into {} lines".format(datetime.now().time(), count))

# close database
conn.commit()
conn.close()