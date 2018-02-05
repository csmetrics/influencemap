import sqlite3
from datetime import datetime
from collections import Counter
import operator
import sys
import re
import json
import entity_type as et 
from difflib import SequenceMatcher

db_PAA = '/localdata/u5798145/influencemap/paper.db'
#db_Authors = '/localdata/common/authors_test.db'
db_Authors = '/localdata/u6363358/data/authors.db'
db_key = '/localdata/u6363358/data/paperKeywords.db'
db_FName = '/localdata/u6363358/data/FieldOfStudy.db'
db_Jour = '/localdata/u6363358/data/Journals.db'
db_conf = '/localdata/u6363358/data/Conference.db'
db_aff = '/localdata/u6363358/data/Affiliations.db'
db_myPAA = '/localdata/u6363358/data/paperAuthorAffiliations.db'

saved_dir = '/localdata/common/savedFileAuthor.json'

temp_nameList = {}

checked_name = {}

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


def getPaperName(pID):
    dbPAA = sqlite3.connect(db_PAA, check_same_thread = False)
    curP = dbPAA.cursor()
    #print("{} getting paperTitle and date".format(datetime.now()))
    if len(pID) == 1:
        #print("SELECT paperTitle, publishedDate FROM papers WHERE paperID == '" + pID[0] + "'")
        curP.execute("SELECT paperID, paperTitle, publishedYear, publishedDate, conferenceID FROM papers WHERE paperID == '" + pID[0] + "'")
    else:
        #print(removeCon("SELECT paperTitle, MAX(publishedDate) FROM papers WHERE paperID IN {}".format(tuple(pID))))
        curP.execute(removeCon("SELECT paperID, paperTitle, publishedYear, publishedDate, conferenceID FROM papers WHERE paperID IN {}".format(tuple(pID))))
    res = curP.fetchall()
    curP.close()
    dbPAA.close()
    #recent = max(res, key=lambda x: x[-1])
    return res

def getAuthor(name, cbfunc=None, nonExpandAID=[], expand=False,use_cache=True, yearStart=0, yearEnd=2016):
    
    if len(name) == 0:
        if expand: return ([],[],[])
        else: return ([],[])

    name = ' '.join([x for x in name.split(' ') if x != ''])


    finalresult = [] #finalresult is a list of dict
    aIDpaper = {} #aIDpaper is a dict of entity:[(pID, title, year)]
    
    if use_cache:
        inside = False
        theName = ''
        with open("/localdata/common/authInfoCache/authNameList.txt") as nameList:
            for line in nameList:
                if isSame(line.strip().lower(), name.lower()):
                    inside = True
                    theName = line
                    break
        if inside: 
            name = name.lower()    
            cacheName = '_'.join(theName.split(' '))[0:-1]
            print(cacheName)
            with open("/localdata/common/authInfoCache/" + cacheName + ".json", 'r') as cache:
                cacheData = json.load(cache) #cacheData = aID:(name, {name, aID, numpaper, aff, field, recentPaper, date}, [(paperID, title, year)]
                for key in cacheData:
                    if not expand:
                        tsName = cacheData[key][0]
                        if tsName == name:
                            finalresult.append(cacheData[key][1])
                            aIDpaper[et.Entity(key, et.Entity_type.AUTH)] = cacheData[key][2]
                      

                    else:
                        tsName = cacheData[key][0]
                        if isSame(tsName, name) and tsName != name:
                            finalresult.append(cacheData[key][1])
                            aIDpaper[et.Entity(key, et.Entity_type.AUTH)] = cacheData[key][2]
                

                for dic in finalresult: print(dic)
                if not expand: return (finalresult, aIDpaper, [])
                else: return (finalresult, aIDpaper)                       
                                                

    dbPAA = sqlite3.connect(db_myPAA, check_same_thread = False)
    dbA = sqlite3.connect(db_Authors, check_same_thread = False)
    dbK = sqlite3.connect(db_key, check_same_thread = False)
    dbFN = sqlite3.connect(db_FName, check_same_thread = False)
    dbConf = sqlite3.connect(db_conf, check_same_thread = False)
    curP = dbPAA.cursor()
    curA = dbA.cursor()
    curK = dbK.cursor()
    curFN = dbFN.cursor()
    curC = dbConf.cursor()

    name = name.lower()

    #Extracting al the authorID whose name matches

    allAuthor = []
    authorNotSameName = []
    lstN = name.split(' ')[-1]
    fstN = name.split(' ')[0]
    fstLetter = fstN[0]
    #middle = name.split(' ')[1:-1]
    print("{} getting all the aID".format(datetime.now()))
    cbfunc(10, "getting all the aID")
    #curA.execute("SELECT * FROM authors WHERE authorName LIKE '% " + lstN + "' AND isSame(authorName,'" + name + "')")
 
 
    if not expand:
        inputValues = (lstN, fstN + "%", fstLetter + " %")
        #NOTE THE Only query that process user input
        curA.execute("""SELECT authorID, authorName FROM authors WHERE lastName == ? AND (authorName LIKE ? OR authorName LIKE ? )""",inputValues)
        allAuthor = curA.fetchall() #allAuthor is a list of (authorID, authName)
        for a in allAuthor: print(a)
        print("number of author is " + str(len(allAuthor))) 
        authorNotSameName = [x for x in allAuthor if x[1] != name]

        allAuthor = [x for x in allAuthor if x[1] == name]
        
    else:
        allAuthor = nonExpandAID
  
    
    print("{} finished getting all the aID".format(datetime.now()))
    cbfunc(30, "finished getting all the aID")
    author = {} #authorID is the key and authorName is the value

    for a in allAuthor:
        author[a[0]] = a[1]

    aID = list(author.keys())
 
    print("{} getting all the (authorID, paperID, affiliationName)".format(datetime.now()))
    cbfunc(40, "getting all the (authorID, paperID, affiliationName)")
    curP.execute(removeCon("SELECT auth_id, paper_id, affNameOri FROM paa WHERE auth_id IN {}".format(tuple(aID))))
    result = curP.fetchall()

    finalres = [] #finalres is a list of (authorName, authorID, pID, affName)

    #Putting the authorName into the tuples
    for tuples in result:
        finalres.append((author[tuples[0]],tuples[0],tuples[1],tuples[2]))

    #Getting paperInfo and most related fields    
    paperIDs = list(set(map(lambda x:x[2], finalres)))
    print("{} getting all the paperInfo".format(datetime.now()))
    cbfunc(50, "getting all the paperInfo")
    tem_paperNames = getPaperName(paperIDs) #tem_paperNames is a [(paperID, title, year, date, conferenceID)]
    print("{} getting all conference related".format(datetime.now()))
    cbfunc(60, "getting all conference related")
    confIDs = list(set(map(lambda x:x[-1], tem_paperNames)))
    curC.execute(removeCon("SELECT ConfID, FullName FROM ConferenceSeries WHERE ConfID IN {}".format(tuple(confIDs))))
    cIDN = curC.fetchall() #cIDN is a list of (ConfID, confName)
    paperNames = [] #paperNames is a list of (paperID, title, year, date, conferenceName)

    for tup in tem_paperNames:
        cid = tup[-1]
        hascID = False
        for t in cIDN:
            if t[0] == cid:
                 paperNames.append((tup[0],tup[1],tup[2],tup[3],t[1]))
                 hascID = True
                 break
        if not hascID:
            paperNames.append((tup[0],tup[1],tup[2],tup[3],''))    

    print("{} getting related fieldIDs".format(datetime.now()))  
    cbfunc(70, "getting related fieldIDs")
    curK.execute(removeCon("SELECT PaperID, FieldID FROM paperKeywords WHERE PaperID IN {}".format(tuple(paperIDs))))
    pIDfID = curK.fetchall() #is a [(pID, fieldID)]
    fIDs = list(set(map(lambda x:x[1], pIDfID)))
    pIDfN = [] #a list of (pID, fName)
    if len(fIDs) > 0:
        curFN.execute(removeCon("SELECT FieldName, FieldID FROM FieldOfStudy WHERE FieldID IN {}".format(tuple(fIDs))))
        fNfID = curFN.fetchall()
        for pf in pIDfID:
            for nid in fNfID:
                if pf[1] == nid[1]:
                    pIDfN.append((pf[0],nid[0]))
                    break
    
    
    tempres = [] #tempres is a list of (authName, authID, paperID, affName, title, year, date, confName) 
    for tup in finalres:
        for t in paperNames:
            if tup[2] == t[0]:
                tempres.append((tup[0],tup[1],tup[2],tup[3],t[1],t[2],t[3],t[4]))
    
    # to modify aIDpaper
    temp_aIDpaper = {}
    for tup in tempres:
        tsID = tup[1]
        tsPID = []
        for t in tempres:
            if t[1] == tsID:
                 tsPID.append(t[2])
        temp_aIDpaper[tsID] = tsPID

    #to modify finalresult
    print("{} getting related fields".format(datetime.now()))
    cbfunc(90, "getting related fields")
    used_ids = []
    for tup in tempres:
        ids = tup[1]
        if ids in used_ids:
            continue
        numpaper = len(temp_aIDpaper[ids])
        paperIDs = temp_aIDpaper[ids]
        fields = []
        for p in paperIDs:
            for ps in pIDfN:
                if p == ps[0]:
                    fields.append(ps[1])
        tem_field = []
        used_fname = []
        for fname in fields:
            if fname in used_fname:
                continue
            tsName = fname
            num = 0
            for f in fields:
                if f == tsName: 
                   num = num + 1
            tem_field.append((tsName, num))
            used_fname.append(fname)
        tem_field = sorted(tem_field, key=lambda x:x[1], reverse=True)
        field = []
        if len(tem_field) >= 3:
            field = tem_field[0:3]            
        else:
            field = tem_field
        aff = []
        paperInfo = []
        for t in tempres:
            if t[1] == ids:
                 if t[3] != '': aff.append(t[3])
                 paperInfo.append({'paperID':t[2],'affiliatoins':t[3],'title':t[4],'year':t[5],'date':t[6],'confName':t[7]}) #paperInfo is a list of (paperID, affname, title, year, date, confName)
        if len(aff) > 0:
            affiliation = mostCommon(aff)
        else:
            affiliation = ''
        recent = max(paperInfo, key=lambda x:x['date'])
        aIDpaper[et.Entity(ids, et.Entity_type.AUTH)] = paperInfo
        finalresult.append({'name':name,'id':ids,'numpaper':numpaper,'affiliation':affiliation,'field':field,'recentPaper':recent['title'],'publishedDate':recent['date']})    
        used_ids.append(ids)        

    for dic in finalresult: print(dic)
    
    for key in aIDpaper:
        infos = aIDpaper[key]
        for entity in infos: print(entity)
     

    print("{} done".format(datetime.now()))
    cbfunc(100, "done")
    curC.close()
    dbConf.close()
    curK.close()
    dbK.close()
    curFN.close()
    dbFN.close()
    curP.close()    
    dbPAA.commit()
    dbPAA.close()
    curA.close()
    dbA.commit()
    dbA.close()
    
    if not expand: return (finalresult, aIDpaper, authorNotSameName) #if not expand, will also return a list of authorID whose name are not exactly the same
    else: return (finalresult,aIDpaper) 


def getJournal(name, a=None):
    if len(name) == 0: return []
    name = ' '.join([x for x in name.split(' ') if x != ''])
    dbJ = sqlite3.connect(db_Jour, check_same_thread = False)
    curJ = dbJ.cursor()
    dbJ.create_function("match",2,match)
    journals = []
    print("{} getting the journalIDs".format(datetime.now()))
    #NOTE query that process user input
    curJ.execute("""SELECT * FROM Journals WHERE match(?, JournalName)""", [name])
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

def getJourPID(jIDs, yearStart=0, yearEnd=2016): #thie function takes in a list of journalID, and produce a dict of jID:[pID]
    dbPAA = sqlite3.connect(db_PAA, check_same_thread = False)
    curP = dbPAA.cursor()
    print("{} getting papers".format(datetime.now()))
    curP.execute(removeCon("SELECT paperID, paperTitle, publishedYear, journalID FROM papers WHERE journalID IN {}".format(tuple(jIDs))))
    paperJourID = curP.fetchall()
    print("{} finished getting paper".format(datetime.now()))
    papers = list(map(lambda x:((x[0],x[1],x[2]),x[3]), paperJourID))

    jID_papers = {}
    for paper, jID in papers:
        if int(paper[-1]) >= yearStart and int(paper[-1]) <= yearEnd: 
            jID_papers.setdefault(jID,[]).append({'title':paper[1], 'paperID':paper[0],'year':paper[2]})

    output = {}
    for key in jID_papers:
        output[et.Entity(key, et.Entity_type.JOUR)] = jID_papers[key]

    for key in output: print(output[key])

    curP.close()
    dbPAA.close()
    return jID_papers #jID_papers is a dict of jID:[(pID, paperTitle, year)]

def getConf(name, a=None):
    if len(name) == 0: return []
    name = ' '.join([x for x in name.split(' ') if x != ''])
    name = name.upper()
    dbConf = sqlite3.connect(db_conf, check_same_thread = False)
    curC = dbConf.cursor()
    dbConf.create_function("match",2,match)
    print("{} getting conferenceID".format(datetime.now()))
    #NOTE query that process user input
    curC.execute("""SELECT * FROM ConferenceSeries WHERE ShortName == ? OR match(?, Fullname)""", (name,name))
    conference = list(map(lambda x: (x[0],x[2]),curC.fetchall()))
     
    temp = [x for x in conference if x[1].lower() == name.lower()]
    conference = [x for x in conference if x[1].lower() != name.lower()]
    conference = temp + conference

    output = []
    
    for tup in conference:
        output.append({'id':tup[0],'name':tup[1]})        
    
    for dic in output: print(dic)


    curC.close()
    dbConf.close()
    return output #a list of {'id':confID, 'name':confName}
    

def getConfPID(cIDs, yearStart=0, yearEnd=2016): #this function takes in a list of cID, and produce a dict of cID:[pID]
    dbP = sqlite3.connect(db_PAA,check_same_thread = False)
    curP = dbP.cursor()
    #cIDs = ["'"+cID+"'" for cID in cIDs]
    print("{} start getting papers".format(datetime.now()))
    #print("SELECT paperID, paperTitle, publishedYear, conferenceID FROM papers WHERE conferenceID IN ({})".format(', '.join(cIDs)))
    #curP.execute("SELECT paperId, paperTitle, publishedYear,conferenceID FROM papers WHERE conferenceID IN ({})".format(', '.join(cIDs)))
    print(removeCon("SELECT paperID, paperTitle, publishedYear, conferenceID FROM papers WHERE conferenceID IN {}".format(tuple(cIDs))))
    curP.execute(removeCon("SELECT paperID, paperTitle, publishedYear, conferenceID FROM papers WHERE conferenceID IN {}".format(tuple(cIDs))))
    papersConfID = curP.fetchall()
    papers = list(map(lambda x:((x[0],x[1],x[2]),x[3]),papersConfID))
    print("{} finished getting papers".format(datetime.now()))
    cID_papers = {}
    
    for pID, cID in papers:
        if pID[-1] != '':
            if int(pID[-1]) >= yearStart and int(pID[-1]) <= yearEnd: 
                cID_papers.setdefault(cID,[]).append({'title':pID[1],'paperID':pID[0],'year':pID[2]})
        
    output = {}
    for key in cID_papers:
        output[et.Entity(key, et.Entity_type.CONF)] = cID_papers[key]

    for key in output: print(output[key])

    curP.close()
    dbP.close()
    return cID_papers #cID_papers is a dict of cID:[(pID, paperTitle, year)]
     

def getAff(aff, a=None):
    if len(aff) == 0: return []
    aff = ' '.join([x for x in aff.split(' ') if x != ''])
    dbA = sqlite3.connect(db_aff, check_same_thread = False)
    dbA.create_function("match",2,match)
    dbA.create_function("matchForShort", 2, matchForShort)
    curA = dbA.cursor()
    #NOTE query that process user input
    curA.execute("""SELECT AffiliationID, AffiliationName FROM Affiliations WHERE match(AffiliationName, ?) OR matchForShort(?, AffiliationName) OR match(?, AffiliationName)""" , (aff,aff,aff))    
    affiliations = curA.fetchall()
    curA.close()
    dbA.close()
    temp = [x for x in affiliations if x[1] == aff] 
    affiliations = [x for x in affiliations if x[1] != aff]
    affiliations = temp + affiliations
    affiliations = [{'id': x[0], 'name': x[1]} for x in affiliations]
    for tup in affiliations:
        print(tup)
    return affiliations #affiliations is a list of {'id': affID, 'name': affName)

def nameHandler(aff, name):
    #this function takes in the name of the affiliation the user selected, and output a name which includes all the key word the user input
    aff = aff.lower().split(' ')
    name = name.lower().split(' ')
    exist = False
    for word in name:
        for w in aff:
            if similar(word,w):
                exist = True
                break
        if not exist:
            break
    if exist: 
       # print(' '.join(aff))
        return ' '.join(aff)
    
    short = ''.join([x[0] for x in name if x != 'the' and x != 'of' and x != 'for'])
    keyword = ' '.join([x for x in aff if x != short])
    #print(keyword + ' ' + ' '.join(name))
    return (keyword + ' ' + ' '.join(name))


def getAffPID(chosen,name): # chosen is the list of dict chosen by the user, name is the user input
    dbPAA = sqlite3.connect(db_myPAA, check_same_thread = False)
    dbPAA.create_function("matchList",1,matchList)
    curP = dbPAA.cursor()
    affID = list(map(lambda x:x['id'], chosen))
    affName = list(map(lambda x:x['name'], chosen))
    global temp_nameList
    temp_nameList = set(map(lambda x:nameHandler(name, x),affName))    
    curP.execute(removeCon("SELECT paper_id, affi_id, affNameOri FROM paa WHERE affi_id IN {}".format(tuple(affID))) + " AND matchList(affNameOri)")     
    papers = curP.fetchall()
    curP.close()
    dbPAA.close()
    affID_pID = {}
    
    affIDpIDList = list(map(lambda x: (x[0],x[1]), papers))
    for paper, aff in affIDpIDList:
        affID_pID.setdefault(aff,[]).append({'id':paper})
     
    output = {}
    for key in affID_pID:
        output[et.Entity(key, et.Entity_type.AFFI)] = affID_pID[key]

    for key in output: print(output[key])
   
               
    return affID_pID #affID_pID is a dict of affID:[pID]


def match(name1, name2): # name1 must be in name2
    name1tem = name1.lower()
    name2tem = name2.lower()
    ls1 = name1tem.split(' ')
    ls2 = name2tem.split(' ')
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

def matchList(name2):
    #instanceList = temp_nameList
    for n in temp_nameList:
        if match(n,name2): return True
    return False

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
    trial = getAff('anu')
    cID = [x for x in trial if x['name'] == 'australian national university']
    x = getAffPID(cID,'anu') 
