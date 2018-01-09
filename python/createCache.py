import json
import mkAff
from datetime import datetime

aName = ["stephen m blackburn","antony l hosking"]

out_dir = '/localdata/u6363358/data/savedFile.json'


with open(out_dir) as output:
     data_exist = json.load(output)
     #data_exist = {}

for aN in aName:
    res = mkAff.getAuthor(aN,False)
    data_exist[aN] = res

with open(out_dir,'w') as output:
    json.dump(data_exist, output, indent = 2)


        
 
