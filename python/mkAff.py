import sqlite3
from datetime import datetime
from collections import Counter
import operator
import sys
import re
import json
from difflib import SequenceMatcher

db_PAA = '/localdata/u5798145/influencemap/paper.db'
db_Authors = '/localdata/common/authors_test.db'
db_key = '/localdata/u6363358/data/paperKeywords.db'
db_FName = '/localdata/u6363358/data/FieldOfStudy.db'
db_Jour = '/localdata/u6363358/data/Journals.db'
db_conf = '/localdata/u6363358/data/Conference.db'
db_aff = '/localdata/u6363358/data/Affiliations.db'

temp_saved_auInfo = '/localdata/common/temp_saved_auInfo.json'
temp_saved_aIDpID = '/localdata/common/temp_saved_aIDpID.json'
temp_saved_aID = '/localdata/common/temp_saved_aID.json'

saved_dir = '/localdata/common/savedFileAuthor.json'

def removeCon(lst):
   if lst[-2] == ",":
       return lst[:-2] + ")"
   else:
       return lst


def isSame(name1, name2):
    #if name1 in memory: return memory[name1]
    #if not name1.endswith(name2.split(' ')[-1]):
        # memory[name1] = False
         #return False
    
    ls1 = name1.split(' ')
    ls2 = name2.split(' ')
    if len(ls2[0]) == 1 or len(ls1[0]) == 1:
        return ls2[0][0] == ls1[0][0] and ls2[-1] == ls1[-1]
    else:
        return ls2[0] == ls1[0] and ls2[-1] == ls1[-1]


def mostCommon(lst):
    return max(set(lst),key=lst.count)

def getField(pID):
    dbK = sqlite3.connect(db_key, check_same_thread = False)
    dbN = sqlite3.connect(db_FName, check_same_thread = False)
    curK = dbK.cursor()
    curFN = dbN.cursor()
    if len(pID) == 1:
         #print("{} Getting fieldID".format(datetime.now()))
         curK.execute("SELECT FieldID FROM paperKeywords WHERE PaperID = '" + pID[0] + "'")
         #curK.execute(removeCon("SELECT FieldID FROM paperKeywords WHERE PaperID IN {}".format(tuple(pID))))
    else:
         #print("{} Getting fieldID".format(datetime.now()))
         curK.execute(removeCon("SELECT FieldID FROM paperKeywords WHERE PaperID IN {}".format(tuple(pID))))
         #curK.execute("SELECT FieldID FROM paperKeywords WHERE PaperID == '" + pID[0] + "'")
    res = list(map(lambda x: x[0],curK.fetchall()))
    #print("{} finished getting fieldID".format(datetime.now()))
    #print("{} getting fieldName".format(datetime.now()))
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
    #print("{} getting paperTitle and date".format(datetime.now()))
    if len(pID) == 1:
        curP.execute("SELECT paperTitle, publishedDate FROM papers WHERE paperID == '" + pID[0] + "'")
    else:
        curP.execute(removeCon("SELECT paperTitle, MAX(publishedDate) FROM papers WHERE paperID IN {}".format(tuple(pID))))
    #print("{} finished getting paperTitle and date".format(datetime.now()))
    title = curP.fetchall()
    dbPAA.commit()
    dbPAA.close()
    if len(title) > 0:
        return (title[0][0], title[0][1])
    else: return ('','')

def getAuthor(name,cbfunc,expand=False,use_cache=False):
    if use_cache:
       with open(saved_dir,'r') as savedFile:
           data_exist_author = json.load(savedFile)
           for key in data_exist_author:
                if isSame(key,name):
                     if expand:
                         for dic in data_exist_author[key][0]: #data_exist_author is {name:({auInfo},{aID:[pID]})}
                             print(dic) 
                         return data_exist_author[key]
                     else:
                         auInfo = data_exist_author[key][0]
                         auInfoSame = []
                         for dic in auInfo:
                             if dic['name'] == name: auInfoSame.append(dic)
                         for dic in auInfoSame: print(dic)
                         return (auInfoSame, data_exist_author[key][1])
                    

    dbPAA = sqlite3.connect(db_PAA, check_same_thread = False)
    dbA = sqlite3.connect(db_Authors, check_same_thread = False)
    #dbA.create_function("compareMiddle",2,compareMiddle)
    dbA.create_function("similar",2,similar)
    curP = dbPAA.cursor()
    curA = dbA.cursor()
    name = name.lower()

    #Extracting al the authorID whose name matches

    allAuthor = []
    lstN = name.split(' ')[-1]
    fstN = name.split(' ')[0]
    fstLetter = fstN[0]
    #middle = name.split(' ')[1:-1]
    print("{} getting all the aID".format(datetime.now()))
    cbfunc("getting all the aID")
    #curA.execute("SELECT * FROM authors WHERE authorName LIKE '% " + lstN + "' AND isSame(authorName,'" + name + "')")

    if not expand:
        curA.execute("SELECT * FROM authors WHERE authorName LIKE '% " + lstN + "' AND (authorName LIKE '" + fstN + "%' OR substr(authorName, 1, 2) == '" + fstLetter + " ')")
        allAuthor = curA.fetchall()
        authorNotSameName = [x for x in allAuthor if x[1] != name]

        allAuthor = [x for x in allAuthor if x[1] == name]

        with open(temp_saved_aID,'w') as saved_aID:
             if len(authorNotSameName) != 0:
                 json.dump(authorNotSameName,saved_aID,indent = 2)
             else: json.dump([],saved_aID,indent = 2)
    else:
        with open(temp_saved_aID) as saved_aID:
             allAuthor = json.load(saved_aID)
    print("{} finished getting all the aID".format(datetime.now()))
    cbfunc("finished getting all the aID")
    author = {} #authorID is the key and authorName is the value

    for a in allAuthor:
         author[a[0]] = a[1]

    aID = list(author.keys())

    result = []
    print("{} getting all the (authorID, paperID, affiliationName)".format(datetime.now()))
    cbfunc("getting all the (authorID, paperID, affiliationName)")
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
    cbfunc("counting the number of paper published by an author")
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
    cbfunc("finish counting, getting the fieldName and recent paper")
    for tuples in tempres:
        recent = getPaperName(tuples[-1]) #a tuple (paperName, date)
        finalresult.append({'name':tuples[0],'authorID':tuples[1],'numpaper':tuples[2],'affiliation':tuples[3],'field':getField(tuples[4]),'recentPaper':recent[0],'publishedDate':recent[1]})
    print("{} done".format(datetime.now()))
    cbfunc("done")
    dbPAA.commit()
    dbA.commit()
    dbPAA.close()
    dbA.close()
    '''
    if not expand:
         with open(temp_saved_auInfo, 'w' ) as saved_auInfo:
              json.dump(finalresult, saved_auInfo, indent = 2)
         with open(temp_saved_aIDpID, 'w') as saved_aIDpID:
              json.dump(aIDpIDDict, saved_aIDpID, indent = 2)
    else:
         with open(temp_saved_auInfo) as saved_auInfo:
              data_exist_auInfo = json.load(saved_auInfo)
         for dic in finalresult:
              data_exist_auInfo.append(dic)
         with open(temp_saved_aIDpID) as saved_aIDpID:
              data_exist_aIDpID = json.load(saved_aIDpID)
         for key in aIDpIDDict:
              data_exist_aIDpID[key] = aIDpIDDict[key]
         finalresult = data_exist_auInfo
         aIDpIDDict = data_exist_aIDpID
    '''
    for dic in finalresult: #finalresult is a list of dict
         print(dic)
    print(len(finalresult))
    print(len(aIDpIDDict))

    return (finalresult,aIDpIDDict)


def getJournal(name):
    dbJ = sqlite3.connect(db_Jour, check_same_thread = False)
    curJ = dbJ.cursor()
    dbJ.create_function("match",2,match)
    journals = []
    print("{} getting the journalIDs".format(datetime.now()))
    curJ.execute("SELECT * FROM Journals WHERE match('" + name + "', JournalName)")
    #curJ.execute("SELECT * FROM Journals WHERE JournalName == '" + name + "'")
    journals = curJ.fetchall()
    
    temp = [x for x in journals if x[1].lower() == name.lower()]
    journals = [x for x in journals if x[1].lower() != name.lower()]
    journals = temp + journals   

    print("{} finished getting jID".format(datetime.now()))
    curJ.close()

    for tup in journals:
        print(tup)
    return journals #journals is a list of (journalID, journalName)

def getJourPID(jIDs): #thie function takes in a list of journalID, and produce a dict of jID:[pID]
    dbPAA = sqlite3.connect(db_PAA, check_same_thread = False)
    curP = dbPAA.cursor()
    print("{} getting papers".format(datetime.now()))
    curP.execute(removeCon("SELECT paperID, journalID FROM papers WHERE journalID IN {}".format(tuple(jIDs))))
    papers = curP.fetchall()
    print("{} finished getting paper".format(datetime.now()))
    jID_papers = {}
    for pID, jID in papers:
        jID_papers.setdefault(jID,[]).append(pID)
    curP.close()
    return jID_papers #a dict of jID:[pID]



def getConf(name):
    name = name.upper()
    dbConf = sqlite3.connect(db_conf, check_same_thread = False)
    dbP = sqlite3.connect(db_PAA, check_same_thread = False)
    curC = dbConf.cursor()
    curP = dbP.cursor()
    dbConf.create_function("match",2,match)
    print("{} getting conferenceID".format(datetime.now()))
    print("SELECT * FROM ConferenceSeries WHERE ShortName == '" + name + "' OR match('" + name + "', Fullname)")
    curC.execute("SELECT * FROM ConferenceSeries WHERE ShortName == '" + name + "' OR match('" + name + "', Fullname)")
    conference = list(map(lambda x: (x[0],x[2]),curC.fetchall()))
     
    temp = [x for x in conference if x[1].lower() == name.lower()]
    conference = [x for x in conference if x[1].lower() != name.lower()]
    conference = temp + conference
     
    for tup in conference:
        print(tup)
    
    curC.close()
    return conference #a list of (confID, confName)
    

def getConfPID(cIDs): #this function takes in a list of cID, and produce a dict of cID:[pID]
    dbP = sqlite3.connect(db_PAA,check_same_thread = False)
    curP = dbP.cursor()
    print("{} start getting papers".format(datetime.now()))
    curP.execute("SELECT paperId, conferenceID FROM papers WHERE conferenceID IN {}".format(tuple(cID)))
    papers = curP.fetchall()
    print("{} finished getting papers".format(datetime.now()))
    cID_papers = {}
    for pID, cID in papers:
        cID_papers.setdefault(cID,[]).append(pID)
    curP.close()
    return cID_papers #cID_papers is a dict of cID:[pID]
     


def getAff(aff):
    dbP = sqlite3.connect(db_PAA, check_same_thread = False)
    dbA = sqlite3.connect(db_aff, check_same_thread = False)
    curP = dbP.cursor()
    curA = dbA.cursor()
    aff = aff.lower()
    dbA.create_function("match",2,match)
    dbP.create_function("contains",2,contains)
    #dbP.create_function("contains",2,contains)
    print("{} getting affiliationID".format(datetime.now())) #get affiliationID that match the given institution
    print("SELECT AffiliationID, AffiliationName FROM Affiliations WHERE match(AffiliationName, '" + aff + "')" )
    curA.execute("SELECT AffiliationID, AffiliationName FROM Affiliations WHERE match(AffiliationName, '" + aff + "')")
    temp = curA.fetchall()
    affID = list(map(lambda x: x[0], temp))
    if len(affID) != 0: affiliationName = temp[0][1] #get the normalized affiliationName
    else: return {}
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
    name1 = name1.lower()
    name2 = name2.lower()
    ls1 = name1.split(' ')
    ls2 = name2.split(' ')
    ls1 = [x for x in ls1 if x != 'the' and x != 'college' and x != 'department' and x != 'of' and x != 'and' and x != 'conference' and x != 'journal' and x != 'university']
    ls2 = [x for x in ls2 if x != 'the' and x != 'college' and x != 'department' and x != 'of' and x != 'and' and x != 'conference' and x != 'journal' and x != 'university']
    for word in ls1:
        exist = False
        for w in ls2:
            if similar(word,w):
                exist = True
                break
        if not exist: return False
    return True



def similar(name1, name2):
    return SequenceMatcher(None,name1,name2).ratio() >= 0.9


def contains(name1, name2):
    name2 = name2.lower()
    ls1 = name1.split(' ')
    ls1 = [x for x in ls1 if x != 'the' and x != 'college' and x != 'department' and x != 'of' and x != 'and']
    for word in ls1:
        if word not in name2:
             return False
    return True

if __name__ == '__main__':
    trial = getAuthor('stephen m blackburn',lambda x:x, True, False)
