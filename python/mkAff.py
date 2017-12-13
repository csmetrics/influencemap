import sqlite3
from datetime import datetime

db_PAA = '/localdata/u5798145/influencemap/paper.db'

db_Authors = '/localdata/common/authors_test.db'

db_key = '/localdata/u6363358/data/PaperKeywords.db'

db_FName = '/localdata/u6363358/data/FieldOfStudy.db'

dbPAA = sqlite3.connect(db_PAA)

dbA = sqlite3.connect(db_Authors)

dbK = sqlite3.connect(db_key)

dbN = sqlite3.connect(db_FName)

name = 'antony l hosking'

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

def removeCon(lst):
   if lst[-2] == ",":
       return lst[:-2] + ")"
   else: 
       return lst

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

print(removeCon("SELECT authorID, paperID, affiliationNameOriginal FROM paperAuthorAffiliations WHERE authorID IN {}".format(tuple(aID))))
curP.execute(removeCon("SELECT authorID, paperID, affiliationNameOriginal FROM paperAuthorAffiliations WHERE authorID IN {}".format(tuple(aID))))

result = curP.fetchall()

finalres = []

print("{} start counting".format(datetime.now()))
for tuples in result:
   finalres.append((author[tuples[0]], tuples[0], tuples[1], tuples[2]))
  # print((author[tuples[0]], tuples[0], tuples[1], tuples[2]))

curP.close()

finalresult = []

def mostCommon(lst):
    return max(set(lst),key=lst.count)

curK = dbK.cursor()
curFN = dbN.cursor()

def getField(pID):
    curK.execute(removeCon("SELECT FieldID FROM PaperKeywords WHERE PaperID IN {}".format(tuple(pID))))
    res = curK.fetchall()
    res[:] = [x for x in res if x != '']
    mostFreq = ''
    if len(res) > 0:
        mostFreq = mostCommon(res)[0]
        print("SELECT FieldName FROM FieldOfStudy WHERE FieldID == '" + mostFreq + "'")
        curFN.execute("SELECT FieldName FROM FieldOfStudy WHERE FieldID == '" + mostFreq + "'")
        fname = curFN.fetchall()[0][0]
        return fname
    else:
        return ''

for tuples in finalres:
    currentID = tuples[1]
    if currentID not in list(map(lambda x: x[1],finalresult)):
        count = 0
        tep = []
        pID = []
        for tup in finalres:
           if tup[1] == currentID:
              count += 1
              pID.append(tup[-2])  
              tep.append(tup[-1])
        tep[:] = [x for x in tep if x != '']
        if len(tep) > 0:
            finalresult.append((tuples[0],tuples[1],count,mostCommon(tep),getField(pID)))
        else:
            finalresult.append((tuples[0],tuples[1],count,'',getField(pID)))

finalresult = sorted(finalresult,key=lambda x: x[2],reverse=True)

print("{} finished counting".format(datetime.now()))
for tuples in finalresult:
   print(tuples)

curK.close()
curFN.close()

print("{} done".format(datetime.now()))
















