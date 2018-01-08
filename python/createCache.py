import json
import mkAff

aName = ['stephen m blackburn']

out_dir = '/localdata/u6363358/data/savedFile.json'

aIDpID = {}

for aN in aName:
    res = mkAff.getAuthor(aN)
    with open(out_dir,'w') as output:
       # print("dumping")
        '''
        for dic in res[0]:
            json.dump(dic, output)
        json.dump(res[1],output)
        '''
        json.dump({aN: res}, output)
       # print("finished")


