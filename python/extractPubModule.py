import sys
import sqlite3
from datetime import datetime

data_read_autID = '/localdata/common/authors_test.db'
data_read_paa ='/localdata/u5642715/influenceMapOut/paper.db'
data_write = '/home/u5642715/data_loc/influenceMapOut/sb.txt'

#This file produce bunch od tuples (paperID, authorID) where authorID are the IDs of the authors that match the given name

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

def name_to_papers(name):
    db = sqlite3.connect(data_read_autID)
    cur = db.cursor()
    dbPAA = sqlite3.connect(data_read_paa)
    cursor = dbPAA.cursor()

    results = []
    temp = []
    name = name.lower()
    lstname = name.split(' ')[-1]

    cur.execute("SELECT * FROM authors WHERE authorName LIKE " + '\"' + '%' + lstname + '%' + '\"' + ';')
    temp = cur.fetchall()

    ids =  []
    for tuples in temp:
        if isSame(tuples[-1], name):
              ids.append(tuples[0])

    cursor.execute("SELECT paperID FROM PAA WHERE authorID IN {}".format(tuple(ids)))
    return list(map(lambda t : t[0], cursor.fetchall()))

if __name__ == '__main__':
    name = sys.argv[1]
    print(name_to_papers(name))
