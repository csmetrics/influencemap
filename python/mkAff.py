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
db_myPAA = '/localdata/u6363358/data/paperAuthorAffiliations.db'

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
         print("{} Getting fieldID".format(datetime.now()))
         curK.execute("SELECT FieldID FROM paperKeywords WHERE PaperID = '" + pID[0] + "'")
         #curK.execute(removeCon("SELECT FieldID FROM paperKeywords WHERE PaperID IN {}".format(tuple(pID))))
    else:
         print("{} Getting fieldID".format(datetime.now()))
         curK.execute(removeCon("SELECT FieldID FROM paperKeywords WHERE PaperID IN {}".format(tuple(pID))))
         #curK.execute("SELECT FieldID FROM paperKeywords WHERE PaperID == '" + pID[0] + "'")
    #res = list(map(lambda x: x[0],curK.fetchall()))
    res = curK.fetchall()
    print("{} finished getting fieldID".format(datetime.now()))
    res = list(map(lambda x:x[0],res))
    print("{} getting fieldName".format(datetime.now()))
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
        print("SELECT paperTitle, publishedDate FROM papers WHERE paperID == '" + pID[0] + "'")
        curP.execute("SELECT paperTitle, publishedDate FROM papers WHERE paperID == '" + pID[0] + "'")
    else:
        print(removeCon("SELECT paperTitle, MAX(publishedDate) FROM papers WHERE paperID IN {}".format(tuple(pID))))
        curP.execute(removeCon("SELECT paperTitle, MAX(publishedDate) FROM papers WHERE paperID IN {}".format(tuple(pID))))
    #print("{} finished getting paperTitle and date".format(datetime.now()))
    title = curP.fetchall()
    dbPAA.commit()
    dbPAA.close()
    if len(title) > 0:
        return (title[0][0], title[0][1])
    else: return ('','')

def getAuthor(name,cbfunc=lambda _ : None, nonExpandAID=[], expand=False,use_cache=False):
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
                    

    dbPAA = sqlite3.connect(db_myPAA, check_same_thread = False)
    dbA = sqlite3.connect(db_Authors, check_same_thread = False)
    #dbA.create_function("compareMiddle",2,compareMiddle)
    curP = dbPAA.cursor()
    curA = dbA.cursor()
    name = name.lower()

    #Extracting al the authorID whose name matches

    allAuthor = []
    authorNotSameName = []
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
        for a in allAuthor:
            print(a)
        authorNotSameName = [x for x in allAuthor if x[1] != name]

        allAuthor = [x for x in allAuthor if x[1] == name]
        
    else:
        allAuthor = nonExpandAID
  
    
    print("{} finished getting all the aID".format(datetime.now()))
    cbfunc("finished getting all the aID")
    author = {} #authorID is the key and authorName is the value

    for a in allAuthor:
         author[a[0]] = a[1]

    aID = list(author.keys())

    result = []
    print("{} getting all the (authorID, paperID, affiliationName)".format(datetime.now()))
    cbfunc("getting all the (authorID, paperID, affiliationName)")
    curP.execute(removeCon("SELECT auth_id, paper_id, affNameOri FROM paa WHERE auth_id IN {}".format(tuple(aID))))
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
        print(tuples[0])
        recent = getPaperName(tuples[-1]) #a tuple (paperName, date)
        print("{} finished getting recentPaper".format(datetime.now()))
        finalresult.append({'name':tuples[0],'authorID':tuples[1],'numpaper':tuples[2],'affiliation':tuples[3],'field':getField(tuples[4]),'recentPaper':recent[0],'publishedDate':recent[1]})
    print("{} done".format(datetime.now()))
    cbfunc("done")
    curP.close()    
    dbPAA.commit()
    dbPAA.close()
    curA.close()
    dbA.commit()
    dbA.close()
   
    for dic in finalresult: #finalresult is a list of dict
         print(dic)
    print(len(finalresult))
    print(len(aIDpIDDict))

    if not expand: return (finalresult, aIDpIDDict, authorNotSameName) #if not expand, will also return a list of authorID whose name are not exactly the same
    else: return (finalresult,aIDpIDDict) 


def getJournal(name, a=None):
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
    dbJ.close()

    for tup in journals:
        print(tup)
    
    output = []
   
    for tup in journals:
        temp = {'id':tup[0],'name':tup[1]}
        output.append(temp)

    return output #output is a list of {'id':journalID, 'name':journalName}

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
    dbPAA.close()
    return jID_papers #a dict of jID:[pID]



def getConf(name, a=None):
    name = name.upper()
    dbConf = sqlite3.connect(db_conf, check_same_thread = False)
    curC = dbConf.cursor()
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

    output = []
    
    for tup in conference:
        output.append({'id':tup[0],'name':tup[1]})        
    
    curC.close()
    dbConf.close()
    return output #a list of {'id':confID, 'name':confName}
    

def getConfPID(cIDs): #this function takes in a list of cID, and produce a dict of cID:[pID]
    dbP = sqlite3.connect(db_PAA,check_same_thread = False)
    curP = dbP.cursor()
    cIDs = ["'"+cID+"'" for cID in cIDs]
    print("{} start getting papers".format(datetime.now()))
    curP.execute("SELECT paperId, conferenceID FROM papers WHERE conferenceID IN ({})".format(', '.join(cIDs)))
    papers = curP.fetchall()
    print("{} finished getting papers".format(datetime.now()))
    cID_papers = {}
    for pID, cID in papers:
        cID_papers.setdefault(cID,[]).append(pID)
    curP.close()
    dbP.close()
    return cID_papers #cID_papers is a dict of cID:[pID]
     

def getAff(aff, a=None):
    dbA = sqlite3.connect(db_aff, check_same_thread = False)
    dbA.create_function("match",2,match)
    dbA.create_function("matchForShort", 2, matchForShort)
    curA = dbA.cursor()
    curA.execute("SELECT AffiliationID, AffiliationName FROM Affiliations WHERE match(AffiliationName, '" + aff + "') OR matchForShort('" + aff + "', AffiliationName)" )    
    affiliations = curA.fetchall()
    curA.close()
    dbA.close()
    temp = [x for x in affiliations if x[1] == aff] 
    affiliations = [x for x in affiliations if x[1] != aff]
    affiliations = temp + affiliations
    for tup in affiliations:
        print(tup)
    return affiliations #affiliations is a list of (affID, affName)

def nameHandler(aff, name): #this function takes in the name of the affiliation the user selected, and output a name which includes all the key word the user input
    aff = aff.lower().split(' ')
    name = name.lower().split(' ')
    short = ''.join([x[0] for x in name if x != 'the' and x != 'of' and x != 'for'])
    keyword = ' '.join([x for x in aff if x != short])
    print(keyword + ' ' + ' '.join(name))
    return (keyword + ' ' + ' '.join(name))


def getAffPID(affID,name): # affID is a list of affiliationID obtained by using getAff, name is the name output by nameHandler, which takes in aff: the user input, and name: the affiliationName the user chosed
    dbPAA = sqlite3.connect(db_myPAA, check_same_thread = False)
    dbPAA.create_function("match",2,match)
    curP = dbPAA.cursor()
    #print(removeCon("SELECT paper_id, affi_id, affNameOri FROM paa WHERE affi_id IN {}".format(tuple(affID))))
    curP.execute(removeCon("SELECT paper_id, affi_id, affNameOri FROM paa WHERE affi_id IN {}".format(tuple(affID))) + " AND match('" + name + "', affNameOri)")
    #curP.execute(removeCon("SELECT paper_id, affi_id, affNameOri FROM paa WHERE affi_id IN {}".format(tuple(affID))))     
    papers = curP.fetchall()
    curP.close()
    dbPAA.close()
    affID_pID = {}
    
    affIDpIDList = list(map(lambda x: (x[0],x[1]), papers))
    for paper, aff in affIDpIDList:
        affID_pID.setdefault(aff,[]).append(paper)
    affNameSet = set(map(lambda x:x[2], papers))
    for n in affNameSet:
        print(n)    
                
    return affID_pID #affID_pID is a dict of affID:[pID]

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

def matchForShort(name1, name2):
    name1 = name1.lower().split(' ')
    name2 = name2.lower().split(' ')
    ls2 = [x[0] for x in name2 if x != 'the' and x != 'of' and x != 'for']
    ls2 = ''.join(ls2)
    return ls2 in name1
    


if __name__ == '__main__':
    trial = getAff('computer science australian national university')
    ri = [x for x in trial if x[1] == 'australian national university']
    name = nameHandler('computer science anu',ri[0][1])
    d = getAffPID([ri[0][0]], name)
