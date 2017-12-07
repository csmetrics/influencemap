import sys
import sqlite3

data_read_autID = '/localdata/common/authors_test.db'
data_read_paa ='/localdata/u5798145/influencemap/paper.db'
data_write = '/localdata/u6363358/data/MicrosoftAcademicGraph/foo1.txt'
db = sqlite3.connect(data_read_autID)
cur = db.cursor()
dbPAA = sqlite3.connect(data_read_paa)
fileW = open(data_write,'w')

results = []
temp = []
name = (sys.argv[1]).lower()
lstname = name.split(' ')[-1]

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

print("SELECT * FROM authors WHERE authorName LIKE " + '\"' + '%' + lstname + '%' + '\"' + ';')

cur.execute("SELECT * FROM authors WHERE authorName LIKE " + '\"' + '%' + lstname + '%' + '\"' + ';')
temp = cur.fetchall()

cursor = dbPAA.cursor()
ids =  []
for tuples in temp:
    if isSame(tuples[-1], name):
          print(tuples)
          ids.append(tuples[0])

ids = list(set(ids))

### WHERE condition for getting paperID

num_IDs = len(ids)
print(num_IDs)
def getCond():
##    if num >= 1:
#        return "authorID == '" + ids[num] + "\' or " + getCond(num - 1)
#    else:
#        return "authorID == '" + ids[num] + "\';"
      res = ''
      for id in ids:
         res = res + "authorID == '" + id + "\' or "
      res = res + ";"
      return res


count = 0
#cursor.execute('PRAGMA synchronous = OFF')
while count < num_IDs:
    cursor.execute("SELECT * FROM PAA WHERE authorID == " + "'" + ids[count] + "\'" + ";")
    temp1 = []
    temp1 = cursor.fetchall()
    results = results + temp1
    count += 1

###Write the tuples (paperID, authorID) on a file

for tuples in results:
    print(tuples[0] + ' ' + tuples[1])
    fileW.write(tuples[0] + ' ' + tuples[1] + '\n')

fileW.close()
print('done')

