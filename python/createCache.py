import json
import mkAff
from datetime import datetime

aName = ["j eliot b moss"]

confName = []

jourName = []

affName = []

out_autDir = '/localdata/common/savedFileAuthor.json'

out_confDir = '/localdata/common/savedFileConf.json'

out_jourDir = '/localdata/common/savedFileJour.json'

out_affDir = '/localdata/common/savedFileAff.json'

def save(typ,initial):
    lst = []
    out_dir = ''
    getter_func = lambda x:x
    data_exist = {}
    if typ == 'Author':
        out_dir = out_autDir
        lst = aName
        getter_func = lambda name:getAuthor(name,False)
    if typ == 'Conference':
        out_dir = out_confDir
        lst = confName
        getter_func = lambda name:getConf(name,False)
    if typ == 'Journal':
        out_dir = out_jourDir
        lst = jourName
        getter_func = lambda name:getJour(name,False)
    if typ == 'Affiliation':
        out_dir = out_affDir
        lst = affName
        getter_func = lambda name:getAff(name,False)    
    if not initial:
        with open(out_dir) as output:
            data_exist = json.load(output)

    for name in lst:
        res = getter_func name
        data_exist[name] = res
    
    with open(out_dir,'w') as output:
        json.dump(data_exist,output,indent = 2)

if __name__ == '__main__':
    trial = save("Author",False)
