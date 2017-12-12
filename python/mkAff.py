import sqlite3
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

def isSame(name1, name2):
   ls2 = name2.split(' ')
   ls1 = name1.split(' ')
   middle1 = ls1[1:-1]
   middle2 = ls2[1:-1]
   if ls2[-1] == ls1[-1]:
       if ls2[0] == ls1[0]:
           return compareMiddle(middle1, middle2)
       else:
           return False
   else:
      return False


def compareMiddle(middle1, middle2):
    middleShort1 = ''
    middleShort2 = ''
    for char in middle1:
       middleShort1 = middleShort1 + char[0]
    for char in middle2:
       middleShort2 = middleShort2 + char[0]
    return (middleShort2 in middleShort1) or (middleShort1 in middleShort2)
    





print("{} matching the right name".format(datetime.now()))
for a in allAuthor:
    if isSame(a[1],name):
          author[a[0]] = a[1]      

result = []

aID = []
for a in author:
   aID.append(a)

curP.execute("SELECT authorID, paperID, affiliationNameOriginal FROM paperAuthorAffiliations WHERE authorID IN {} ".format(tuple(aID)))

result = curP.fetchall()


finalres = []

for tup in result: 
    finalres.append((author[tup[0]], tup[0], tup[1], tup[2]))

finalresult = []

for tup in finalres:
    currentA = tup[0]
    count = 0
    for tups in finalres:
        if tups[0] == curentA:
             count += 1
    finalresult.append(tup[0],tup[1],count,tup[2])


curP.close()
print("{} done".format(datetime.now()))

for tup in finalresult:
    print(tup)







































