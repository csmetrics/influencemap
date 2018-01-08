import sqlite3
from datetime import datetime
from collections import Counter
import operator
import sys
import re
import json


db_PAA = '/localdata/u5798145/influencemap/paper.db'
db_Authors = '/localdata/common/authors_test.db'
db_key = '/localdata/u6363358/data/paperKeywords.db'
db_FName = '/localdata/u6363358/data/FieldOfStudy.db'
db_Jour = '/localdata/u6363358/data/Journals.db'
db_conf = '/localdata/u6363358/data/Conference.db'
db_aff = '/localdata/u6363358/data/Affiliations.db'

saved_dir = '/localdata/u6363358/data/savedFile.json'

def removeCon(lst):
   if lst[-2] == ",":
       return lst[:-2] + ")"
   else: 
       return lst


def isSame(name1, name2):
   # if name1 in memory: return memory[name1]
    #if not name1.endswith(name2.split(' ')[-1]):
        # memory[name1] = False
         #return False 
    ls1 = name1.split(' ')
    ls2 = name2.split(' ')           
    if ls2[-1] == ls1[-1]:
         middle1 = ls1[1:-1]
         middle2 = ls2[1:-1]
         if len(ls2[0]) == 1 or len(ls1[0]) == 1:
             if ls2[0][0] == ls1[0][0]:
                  b = compareMiddle(middle1, middle2)
                 # memory[name1] = b
                  return b
             else:
                 #memory[name1] = False
                 return False
         else:
             if ls2[0] == ls1[0]:
                 b =  compareMiddle(middle1, middle2)
                 #memory[name1] = b
                 return b
             else: 
                 #memory[name1] = False
                 return False
    else: 
         #memory[name1] = False
         return False

  

def compareMiddle(m1,m2):
   ms1 = ''
   ms2 = ''
   for char in m1:
      ms1 = ms1 + char[0]
   for char in m2:
      ms2 = ms2 + char[0]
   return (ms1 in ms2) or (ms2 in ms1) 
   
def mostCommon(lst):
    return max(set(lst),key=lst.count)


def getField(pID):
    dbK = sqlite3.connect(db_key, check_same_thread = False)
    dbN = sqlite3.connect(db_FName, check_same_thread = False)
    curK = dbK.cursor()
    curFN = dbN.cursor()
    if len(pID) == 1:
         curK.execute("SELECT FieldID FROM paperKeywords WHERE PaperID = '" + pID[0] + "'") 
         #curK.execute(removeCon("SELECT FieldID FROM paperKeywords WHERE PaperID IN {}".format(tuple(pID))))
    else: 
         curK.execute(removeCon("SELECT FieldID FROM paperKeywords WHERE PaperID IN {}".format(tuple(pID))))
         #curK.execute("SELECT FieldID FROM paperKeywords WHERE PaperID == '" + pID[0] + "'")
    res = list(map(lambda x: x[0],curK.fetchall()))
    if len(res) > 0:
         if len(set(res)) > 1:
            res = sorted(dict(Counter(res)).items(),key=operator.itemgetter(1),reverse=True) #produce a dict filedID: numOfOccur sorted in desending order
            topThree = {}
            for i in res:
                if len(topThree) < 3:
                     topThree[i[0]] = i[1] #topthree contains {fieldID, numPaper}
                else: break
            curFN.execute(removeCon("SELECT FieldName, FieldID FROM FieldOfStudy WHERE FieldID IN {}".format(tuple(map(lambda x: x,topThree)))))
            output = list(map(lambda x: (x[0],topThree[x[1]]),curFN.fetchall()))
         else:
            singleFID = res[0][0]
            curFN.execute("SELECT FieldName, FieldID FROM FieldOfStudy WHERE FieldID == '" + singleFID + "'")
            output = list(map(lambda x: (x[0],len(res)),curFN.fetchall())) 
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
    if len(pID) == 1:
        curP.execute("SELECT paperTitle, publishedDate FROM papers WHERE paperID == '" + pID[0][0] + "'")
    else:
        curP.execute(removeCon("SELECT paperTitle, MAX(publishedDate) FROM papers WHERE paperID IN {}".format(tuple(pID))))
    title = curP.fetchall()
    dbPAA.commit()
    dbPAA.close()
    if len(title) > 0:
        return (title[0][0], title[0][1])
    else: return ('','')


def getAuthor(name):
    saved = json.load(open('/localdata/u6363358/data/savedFile.json'))
    if name in saved:
        fs = saved[name][0]
        for dic in fs:
            print(dic)
        return saved[name]
 
    dbPAA = sqlite3.connect(db_PAA, check_same_thread = False)
    dbA = sqlite3.connect(db_Authors, check_same_thread = False)
    dbA.create_function("isSame",2,isSame)
    curP = dbPAA.cursor()
    curA = dbA.cursor()
    name = name.lower()

    #Extracting al the authorID whose name matches

    allAuthor = []
    lstN = name.split(' ')[-1]
    print("{} getting all the aID".format(datetime.now()))
    curA.execute("SELECT * FROM authors WHERE authorName LIKE '%" + lstN + "' AND isSame(authorName,'" + name + "')")
   
    allAuthor = curA.fetchall()
    print("{} finished getting all the aID".format(datetime.now()))
   
    author = {} #authorID is the key and authorName is the value
    #print("{} matching the right name".format(datetime.now()))
    for a in allAuthor:
         author[a[0]] = a[1]
    #print("{} finished matching".format(datetime.now()))
    
    aID = list(author.keys())
    result = []
    print("{} getting all the (authorID, paperID, affiliationName)".format(datetime.now()))
    curP.execute(removeCon("SELECT authorID, paperID, affiliationNameOriginal FROM weightedPaperAuthorAffiliations WHERE authorID IN {}".format(tuple(aID))))
    result = curP.fetchall()

    aIDpIDDict = {}
    
    finalres = []
    
    #Putting the authorName into the tuples
    for tuples in result:
       finalres.append((author[tuples[0]],tuples[0],tuples[1],tuples[2]))

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
                    pID.append(tup[-2]) #pID contains paperID
                    tep.append(tup[-1]) #tep contatins affiliationNameOriginal
            tep[:] = [x for x in tep if x != '']
            aIDpIDDict[currentID] = pID
            if len(tep) > 0:
                tempres.append((tuples[0],tuples[1],count,mostCommon(tep),pID))
            else:
                tempres.append((tuples[0],tuples[1],count,'',pID))
    
    tempres = sorted(tempres,key=lambda x: x[2],reverse=True)
        
    same = []
    same[:] = [x for x in tempres if x[0] == name]
    tempres[:] = [x for x in tempres if x[0] != name]
    tempres = same + tempres
    
    print("{} finish counting, getting the fieldName and recent paper".format(datetime.now()))
   
    for tuples in tempres:
        recent = getPaperName(tuples[-1]) #a tuple (paperName, date)
        finalresult.append({'name':tuples[0],'authorID':tuples[1],'numpaper':tuples[2],'affiliation':tuples[3],'field':getField(tuples[4]),'recentPaper':recent[0],'publishedDate':recent[1]})
    print("{} done".format(datetime.now()))
    
    dbPAA.commit()
    dbA.commit()  
    dbPAA.close()
    dbA.close()
   
    for dic in finalresult:
        print(dic)
    #print(str(len(memory))) 
   
    return (finalresult,aIDpIDDict)  

def getJournal(name):
    dbPAA = sqlite3.connect(db_PAA, check_same_thread = False)
    dbJ = sqlite3.connect(db_Jour, check_same_thread = False)
    curP = dbPAA.cursor()
    curJ = dbJ.cursor()
    dbJ.create_function("match",2,match)
    print("{} getting the journalIDs".format(datetime.now()))
    curJ.execute("SELECT * FROM Journals WHERE match(JournalName, '" + name + "')")
    jID = list(map(lambda x: x[0],curJ.fetchall()))
    journals = curJ.fetchall()
    print("{} finished getting jID".format(datetime.now()))
    print("{} getting the paper published".format(datetime.now()))
    curP.execute(removeCon("SELECT paperID, journalID FROM papers WHERE journalID IN {}".format(tuple(jID))))
    papers = curP.fetchall()
    print("{} finished getting paper".format(datetime.now()))
    
    #grouping tuples by journalID
    jID_papers = {}
    for pID,jID in papers:
        jID_papers.setdefault(jID,[]).append(pID)

    curP.close()
    curJ.close()

    for k in jID_papers:
        print(jID_papers[k])
    for tup in journals:
        print(tup)
    #jID_papers is a dict {jID, [(pID,pTitle,publishedDate)]}, journal is a list
    #[journalID, journalName]
    return (journals, jID_papers)
 
def getConf(name):
    dbConf = sqlite3.connect(db_conf, check_same_thread = False)
    dbP = sqlite3.connect(db_PAA, check_same_thread = False)
    curC = dbConf.cursor()
    curP = dbP.cursor()
    print("{} getting conferenceID".format(datetime.now()))
    print("SELECT * FROM ConferenceSeries WHERE ShortName == '" + name + "' OR Fullname == '" + name + "'")
    curC.execute("SELECT * FROM ConferenceSeries WHERE ShortName == '" + name + "' OR Fullname == '" + name + "'")
    conference = list(map(lambda x: (x[0],x[2]),curC.fetchall()))
    print("{} finished getting cID".format(datetime.now()))
    cID = conference[0][0]
    print("{} getting papers published".format(datetime.now()))
    
    #print(removeCon("SELECT paperID, paperTitle, publishedDate, conferenceID FROM papers WHERE conferenceID IN {}".format(tuple(cID))))
    curP.execute("SELECT paperID, paperTitle, publishedDate, conferenceID FROM papers WHERE conferenceID == '" + cID + "'")
    papers = curP.fetchall()
    print("{} finished getting paper".format(datetime.now()))
    cID_papers = {}
    cID_papers[cID] = papers
            
    for k in cID_papers:
        print(cID_papers[k])
    return (conference, cID_papers)

    curP.close()
    curC.close()

def getAff(aff):
    dbP = sqlite3.connect(db_PAA, check_same_thread = False)
    dbA = sqlite3.connect(db_aff, check_same_thread = False)
    curP = dbP.cursor()
    curA = dbA.cursor()
    aff = aff.lower()
    dbA.create_function("match",2,match)
    #dbP.create_function("contains",2,contains)
    print("{} getting affiliationID".format(datetime.now())) #get affiliationID that match the given institution
    print("SELECT AffiliationID, AffiliationName FROM Affiliations WHERE match(AffiliationName, '"+ aff + "')" )
    curA.execute("SELECT AffiliationID, AffiliationName FROM Affiliations WHERE match(AffiliationName, '" + aff + "')")
    temp = curA.fetchall()
    affID = list(map(lambda x: x[0], temp))
    affiliationName = temp[0][1] #get the normalized affiliationName
    
    print(affID)
  
    print("{} getting related papers".format(datetime.now())) #get papers related 
    curP.execute(removeCon("SELECT paperID, affiliationNameOriginal FROM weightedPaperAuthorAffiliations WHERE affiliationID IN {}".format(tuple(affID))))
    #Form a dict of affiliationName, pID
    aName_pID = {}
    res = curP.fetchall()
    print("{} finished getting papers".format(datetime.now()))
    
    for pID, aN in res:
        aName_pID.setdefault(aN,[]).append(pID)
    
    #get papers related to the specified department
    aName_pID = {aN:pIDs for (aN,pIDs) in aName_pID.items() if contains(aff,aN)}
    result = {}
    ps = []
    for key in aName_pID:
        ps = ps + (aName_pID[key])
    result[affiliationName] = ps 
    curA.close()
    curP.close() 

    for key in result:
       print((key, result[key]))
    
    return(result) #A dict of aName, [pID]

def match(name1, name2):
    ls1 = name1.split(' ')
    ls2 = name2.split(' ')
    ls1 = [x for x in ls1 if x != 'the' and x != 'college' and x != 'department' and x != 'of' and x != 'and']
    ls2 = [x for x in ls2 if x != 'the' and x != 'college' and x != 'department' and x != 'of' and x != 'and']
    for word in ls1:
        if word not in ls2: return False
    return True

def contains(name1, name2):
    name2 = name2.lower()
    ls1 = name1.split(' ')
    ls1 = [x for x in ls1 if x != 'the' and x != 'college' and x != 'department' and x != 'of' and x != 'and']
    for word in ls1:
        if word not in name2:
             return False
    return True

if __name__ == '__main__':
    trial = getAuthor('stephen m blackburn')
