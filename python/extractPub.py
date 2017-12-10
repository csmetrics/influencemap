import sys
import sqlite3
from datetime import datetime

data_read_autID = '/localdata/common/authors_test.db'
data_read_paa ='/localdata/u5798145/influencemap/paper.db'
data_dest = '/localdata/u6363358/data/MicrosoftAcademicGraph/foo.txt'

db = sqlite3.connect(data_read_autID)

cur = db.cursor()

dbPAA = sqlite3.connect(data_read_paa)

fileW = open(data_dest,'w')

resultPaperID = []

temp = []

name = (sys.argv[1]).lower()

lstname = name.split(' ')[-1]

#This file produce bunch od tuples (paperID, authorID) where authorID are the IDs of the authors that match the given name

#Matching the names given and the authorName
def isSame(name1, name2):
    ls2 = name2.split(' ')
    ls1 = name1.split(' ')
    middle2 = ls2[1:-1]
    middle1 = ls1[1:-1]
    if ls2[-1] == ls1[-1]:
         if ls2[0] == ls1[0]:
             return compareMiddle(middle1, middle2)
         else:
             if len(ls2[0]) == 1 or len(ls1[0]) == 1:
                  if ls2[0][0] == ls1[0][0]:
                      return compareMiddle(middle1,middle2)
                  else:
                      return False
             else:
                  return False
    else:
        return False

def compareMiddle(middle1,middle2):
    middleShort2 = ''
    middleShort1 = ''
    for char in middle2:
        middleShort2 = middleShort2 + char[0]
    for char in middle1:
        middleShort1 = middleShort1 + char[0]
    return (middleShort1 in middleShort2) or (middleShort2 in middleShort1)


###Get the tuples whose authorName contains the last name of the given argv
print("{} Getting the (authorID, authorName) tuples".format(datetime.now()))
cur.execute("SELECT * FROM authors WHERE authorName LIKE " + '\"' + '%' + lstname + '%' + '\"' + ';')
temp = cur.fetchall()
cur.close()

cursor = dbPAA.cursor()
ids =  []
for tuples in temp:
    if isSame(tuples[-1], name):
          ids.append(tuples[0])

ids = list(set(ids))

#Get the paperID from these authorIDs

print("{} Getting the (paperID, authorID) tuples".format(datetime.now()))
cursor.execute("SELECT * FROM PAA WHERE authorID IN {}".format(tuple(ids)))
resultPaperID = cursor.fetchall()
cursor.close()

#Writting down the (paperID, authorID) tuples
print("Writting down (paperID, authorID) to {}".format(data_dest))
for tuples in resultPaperID:
    fileW.write(tuples[0] + "	" + tuples[1] + '\n')

fileW.close()
print("{} done".format(datetime.now()))







