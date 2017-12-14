import sqlite3
from datetime import datetime
from collections import Counter

db_PAA = '/localdata/u5798145/influencemap/paper.db'
db_Authors = '/localdata/common/authors_test.db'
db_key = '/localdata/u6363358/data/PaperKeywords.db'
db_FName = '/localdata/u6363358/data/FieldOfStudy.db'


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
    

def mostCommon(lst):
    return max(set(lst),key=lst.count)


def getField(pID):
    dbK = sqlite3.connect(db_key, check_same_thread = False)
    dbN = sqlite3.connect(db_FName, check_same_thread = False)
    curK = dbK.cursor()
    curFN = dbN.cursor()
    curK.execute(removeCon("SELECT FieldID FROM PaperKeywords WHERE PaperID IN {}".format(tuple(pID))))
    res = list(map(lambda x: x[0],curK.fetchall()))
    if len(res) > 0:
         res = sorted(res,key=Counter(res).get,reverse=True)
         topThree = []
         for element in res:
             if len(topThree) < 3 and element not in topThree:
                 topThree.append(element)
             elif len(topThree) >= 3: break
         curFN.execute(removeCon("SELECT FieldName FROM FieldOfStudy WHERE FieldID IN {}".format(tuple(topThree))))
         output = list(map(lambda x: x[0],curFN.fetchall())) 
         dbK.commit()
         dbN.commit()
         dbK.close()
         dbN.close()
         return output
    else:
         dbK.commit()
         dbN.commit()
         dbK.close()
         dbN.close()
         return []

def getPaperName(pID):
    dbPAA = sqlite3.connect(db_PAA, check_same_thread = False)
    curP = dbPAA.cursor()
    curP.execute("SELECT paperTitle,publishedDate FROM papers WHERE paperID == '" + pID + "'")
    title = curP.fetchall()[0]
    dbPAA.commit()
    dbPAA.close()
    return title


def getAuthor(name):
    dbPAA = sqlite3.connect(db_PAA, check_same_thread = False)
    dbA = sqlite3.connect(db_Authors, check_same_thread = False)
    curP = dbPAA.cursor()
    curA = dbA.cursor()

    #Extracting al the authorID whose name matches

    allAuthor = []
    print("{} getting all the aID".format(datetime.now()))
    curA.execute("SELECT * FROM authors WHERE authorName LIKE" + "'%" + name.split(' ')[-1] + "%'")
    allAuthor = curA.fetchall()
    print("{} finished getting all the aID".format(datetime.now()))
   
    author = {} #authorID is the key and authorName is the value
    print("{} matching the right name".format(datetime.now()))
    for a in allAuthor:
       if isSame(a[1],name):
           author[a[0]] = a[1]
    print("{} finished matching".format(datetime.now()))
    
    aID = list(author.keys())
    result = []
    print("{} getting all the (authorID, paperID, affiliationName, paperWeight)".format(datetime.now()))
    curP.execute(removeCon("SELECT authorID, paperID, affiliationNameOriginal, paperWeight FROM weightedPaperAuthorAffiliations WHERE authorID IN {}".format(tuple(aID))))
    result = curP.fetchall()
 
    finalres = []
    
    #Putting the authorName into the tuples
    for tuples in result:
       finalres.append((author[tuples[0]],tuples[0],tuples[1],tuples[2],tuples[3]))

    #Getting the most frequently appeared affiliation
    tempres = []
    finalresult = []
   
    print("{} counting the number of paper published by an author".format(datetime.now()))
    for tuples in finalres:
        currentID = tuples[1]
        if currentID not in list(map(lambda x:x[1], tempres)):
            count = 0
            tep = []
            pID = []
            for tup in finalres:
                if tup[1] == currentID:
                    count += 1
                    pID.append((tup[-3],tup[-1]))
                    tep.append(tup[-2])
            tep[:] = [x for x in tep if x != '']
            if len(tep) > 0:
                tempres.append((tuples[0],tuples[1],count,mostCommon(tep),pID))
            else:
                tempres.append((tuples[0],tuples[1],count,'',pID))
    
    tempres = sorted(tempres,key=lambda x: x[2],reverse=True)
    print("{} finish counting, getting the fieldName".format(datetime.now()))
   
    for tuples in tempres:
        mostWeight = getPaperName(max(tuples[4],key=lambda x: x[1])[0])
        finalresult.append({'name':tuples[0],'authorID':tuples[1],'numpaper':tuples[2],'affiliation':tuples[3],'field':getField(list(map(lambda x: x[0],tuples[4]))),'mostWeightedPaper':mostWeight[0],'publishedDate':mostWeight[1]})
    print("{} done".format(datetime.now()))
    
    dbPAA.commit()
    dbA.commit()  
    dbPAA.close()
    dbA.close()
   
    for dic in finalresult:
        print(dic)
   
    return finalresult 

