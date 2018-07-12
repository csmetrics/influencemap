import json
import mkAff
from datetime import datetime
import os
aName = ["Tim Berners-Lee", "Martin E Hellman", "Whitfield Diffie","Michael Stonebraker","Leslie Lamport","Silvio Micali","Shafi Goldwasser","Judea Pearl","Leslie G Valiant","Charles P Thacker","Barbara Liskov","Edmund M Clarke","E Allen Emerson","Joseph Sifakis","Frances E Allen","Peter Naur","Vinton G Cerf","Robert E Kahn","Alan Kay","Ronald L Rivest","Afi Shamir","Lenoard M Adleman","Ole Johan Dahl","Kristen Nygaard","Andrew Chi Chih Yao","Frederick P Brooks Jr","Jim Gray","Douglas Engelbart","Amir Pnueli","Manuel Blum","Edward Feigenbaum","Raj Reddy","Juris Hartmanis","Richard E Stearns","Butler W Lampson","Robin Milner","Fernando J Corbato","William Kahan","Ivan Sutherland","John Cocke","John Hopcroft","Robert Tarjan","Richard M Karp","Niklaus Wirth","Ken Thompson","Denis M Ritchie","Stephen A Cook","Edgar F Codd","Tony Hoare","Kenneth E Iverson","Robert W Floyd","John Backus","Micheal O Rabin","Dana S Scott","Allen Newell","Herbert A Simon","Donald E Knuth","Charles W Bachman","Edsger W Dijkstra","John McCarthy","James H Wilkinson","Marvin Minsky","Richard Hamming","Maurice Wilkes","Alan J Perlis"]

test = ["Tim Berners Lee"]

confName = []

jourName = []

affName = []

def save(typ):
    '''
    lst = []
    out_dir = ''
    getter_func = lambda x:x
    data_exist = {}
    
    if typ == 'Author':
        out_dir = out_autDir
        lst = test
        getter_func = lambda name:mkAff.getAuthor(name)
    
    if typ == 'Conference':
        out_dir = out_confDir
        lst = confName
        getter_func = lambda name:mkAff.getConf(name)
    if typ == 'Journal':
        out_dir = out_jourDir
        lst = jourName
        getter_func = lambda name:mkAff.getJoural(name)
    if typ == 'Affiliation':
        out_dir = out_affDir
        lst = affName
        getter_func = lambda name:mkAff.getAff(name)    
    '''
    for name in test:
        nonExpandRes = mkAff.getAuthor(name) #([{name, aID, numpaper, affiliation, field, recentPaper, publishedDate}], {aID:[(paperID, title, year)]}, [aID])
        aIDNotSameName = nonExpandRes[-1]
        resNonExpand = (nonExpandRes[0],nonExpandRes[1])
        expandRes = mkAff.getAuthor(name, nonExpandAID=aIDNotSameName, expand=True)
       
        wholeRes = {}
        for dic in resNonExpand[0]:
            for key in resNonExpand[1]:
                if dic['authorID'] == key.entity_name:
                    wholeRes[dic['name']] = (dic, {key.entity_name:resNonExpand[1][key]})
                    break
        
        for dic in expandRes[0]:
            for key in expandRes[1]:
                if dic['authorID'] == key.entity_name:
                    wholeRes[dic['name']] = (dic, {key.entity_name:expandRes[1][key]})
                    break
            
        lsName = name.split(' ')
        cacheName = '_'.join(lsName)

        with open("/localdata/common/" + cacheName  + ".json", "w+") as out:
            out.write('')

        os.chmod("/localdata/common/" + cacheName + ".json", 0o777)     
        
        with open("/localdata/common/" + cacheName + ".json", 'w') as output:
            json.dump(wholeRes,output,indent = 2)              
        #dump a dict of aID:({name, aID, numpaper, affiliation, field, recent, date}, {aID:[(paperID, title, year)]})
        with open("/localdata/common/authorNameCache.txt","w") as nameList:
            nameList.write(name)


if __name__ == '__main__':
    trial = save("Author")
