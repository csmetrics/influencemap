import sqlite3
import extractPubModule
from datetime import datetime

db_PAA = '/localdata/u5798145/influencemap/paper.db'

db_Authors = '/localdata/common/authors_test.db'

dbPAA = sqlite3.connect(db_PAA)

dbA = sqlite3.connect(db_Authors)

name = 'steve m blackburn'

#Get all the (name, authodID, number of paper, normalised affiliation name)
curP = dbPAA.cursor()

curA = dbA.cursor()

allAuthor = []
print("{} getting all the aID".format(datetime.now()))
print("SELECT * FROM authors WHERE authorName LIKE" + "'%" + name.split(' ')[-1] + "%'")
curA.execute("SELECT * FROM authors WHERE authorName LIKE" + "'%" + name.split(' ')[-1] + "%'")
print("{} finished getting all the aID".format(datetime.now()))
allAuthor = curA.fetchall()

curA.close()

author = {}

print("{} matching the right name".format(datetime.now()))
for a in allAuthor:
    if extractPubModule.isSame(a[1],name):
          author[a[0]] = a[1]      

result = []

aID = []
for a in author:
   aID.append(a)

curP.execute("SELECT authorID, paperID, affiliationNameOriginal FROM paperAuthorAffiliations WHERE authorID IN {}".format(tuple(aID)))

result = curP.fetchall()

finalres = []

for tup in result:
    finalres.append((author[tup[0]], tup[0], tup[1], tup[2]))

curP.close()
print("{} done".format(datetime.now()))

for tup in finalres:
    print(tup)









































