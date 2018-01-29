import os, sys, json
from django.shortcuts import render
from operator import itemgetter
from random import random
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON_DIR = os.path.join(os.path.dirname(BASE_DIR), 'python')
sys.path.insert(0, PYTHON_DIR)

links = [{'source': 'lexing xie', 'target': 'shihfu chang', 'type': 'in', 'weight': 1.0}, {'source': 'lexing xie', 'target': 'changsheng xu', 'type': 'in', 'weight': 0.82022471910112404}, {'source': 'lexing xie', 'target': 'milind r naphade', 'type': 'in', 'weight': 0.033707865168539346}, {'source': 'lexing xie', 'target': 'david m blei', 'type': 'in', 'weight': 0.0}, {'source': 'lexing xie', 'target': 'qi tian', 'type': 'in', 'weight': 0.68539325842696608},
{'source': 'lexing xie', 'target': 'michael i jordan', 'type': 'in', 'weight': 0.0}, {'source': 'lexing xie', 'target': 'john r smith', 'type': 'in', 'weight': 0.30337078651685412}, {'source': 'lexing xie', 'target': 'l r rabiner', 'type': 'in', 'weight': 0.0}, {'source': 'lexing xie', 'target': 'apostol natsev', 'type': 'in', 'weight': 0.19101123595505648}, {'source': 'lexing xie', 'target': 'jon kleinberg', 'type': 'in', 'weight': 0.0},
{'source': 'lexing xie', 'target': 'lyndon kennedy', 'type': 'in', 'weight': 0.23595505617977541}, {'source': 'lexing xie', 'target': 'chongwah ngo', 'type': 'in', 'weight': 0.50561797752808946}, {'source': 'lexing xie', 'target': 'david lowe', 'type': 'in', 'weight': 0.0}, {'source': 'lexing xie', 'target': 'xiansheng hua', 'type': 'in', 'weight': 0.46067415730337069}, {'source': 'lexing xie', 'target': 'george a miller', 'type': 'in', 'weight': 0.0},
{'source': 'lexing xie', 'target': 'ajay divakaran', 'type': 'in', 'weight': 0.43820224719101164}, {'source': 'lexing xie', 'target': 'cees g m snoek', 'type': 'in', 'weight': 0.43820224719101092}, {'source': 'lexing xie', 'target': 'rong yan', 'type': 'in', 'weight': 0.3033707865168544}, {'source': 'lexing xie', 'target': 'wen gao', 'type': 'in', 'weight': 0.41573033707865148}, {'source': 'lexing xie', 'target': 'jure leskovec', 'type': 'in', 'weight': 0.056179775280898937},
{'source': 'lexing xie', 'target': 'thomas hofmann', 'type': 'in', 'weight': 0.0}, {'source': 'lexing xie', 'target': 'thorsten joachims', 'type': 'in', 'weight': 0.0}, {'source': 'lexing xie', 'target': 'alexander g hauptmann', 'type': 'in', 'weight': 0.32584269662921361}, {'source': 'lexing xie', 'target': 'vladimir vapnik', 'type': 'in', 'weight': 0.0}, {'source': 'lexing xie', 'target': 'hari sundaram', 'type': 'in', 'weight': 0.25842696629213491},
{'source': 'shihfu chang', 'target': 'lexing xie', 'type': 'out', 'weight': 1.0}, {'source': 'changsheng xu', 'target': 'lexing xie', 'type': 'out', 'weight': 0.0098375180125362116}, {'source': 'milind r naphade', 'target': 'lexing xie', 'type': 'out', 'weight': 0.39831254996410154}, {'source': 'david m blei', 'target': 'lexing xie', 'type': 'out', 'weight': 0.39392843867590671}, {'source': 'qi tian', 'target': 'lexing xie', 'type': 'out', 'weight': 0.049187590062681037},
{'source': 'michael i jordan', 'target': 'lexing xie', 'type': 'out', 'weight': 0.36805148912119173}, {'source': 'john r smith', 'target': 'lexing xie', 'type': 'out', 'weight': 0.35475658253178655}, {'source': 'l r rabiner', 'target': 'lexing xie', 'type': 'out', 'weight': 0.32720440346044355}, {'source': 'apostol natsev', 'target': 'lexing xie', 'type': 'out', 'weight': 0.31522829457561652}, {'source': 'jon kleinberg', 'target': 'lexing xie', 'type': 'out', 'weight': 0.30154131299295778}, {'source': 'lyndon kennedy', 'target': 'lexing xie', 'type': 'out', 'weight': 0.30018178022414466}, {'source': 'chongwah ngo', 'target': 'lexing xie', 'type': 'out', 'weight': 0.0096236589253071644}, {'source': 'david lowe', 'target': 'lexing xie', 'type': 'out', 'weight': 0.28229399514234349}, {'source': 'xiansheng hua', 'target': 'lexing xie', 'type': 'out', 'weight': 0.16467149716636698}, {'source': 'george a miller', 'target': 'lexing xie', 'type': 'out', 'weight': 0.25278144110473477}, {'source': 'ajay divakaran', 'target': 'lexing xie', 'type': 'out', 'weight': 0.17258428339384174}, {'source': 'cees g m snoek', 'target': 'lexing xie', 'type': 'out', 'weight': 0.15269538828154047}, {'source': 'rong yan', 'target': 'lexing xie', 'type': 'out', 'weight': 0.24000822107659986}, {'source': 'wen gao', 'target': 'lexing xie', 'type': 'out', 'weight': 0.0}, {'source': 'jure leskovec', 'target': 'lexing xie', 'type': 'out', 'weight': 0.2258351961138749},
{'source': 'thomas hofmann', 'target': 'lexing xie', 'type': 'out', 'weight': 0.22455204159050049}, {'source': 'thorsten joachims', 'target': 'lexing xie', 'type': 'out', 'weight': 0.22455204159050049}, {'source': 'alexander g hauptmann', 'target': 'lexing xie', 'type': 'out', 'weight': 0.22257870546743252}, {'source': 'vladimir vapnik', 'target': 'lexing xie', 'type': 'out', 'weight': 0.21813626897362903},
{'source': 'hari sundaram', 'target': 'lexing xie', 'type': 'out', 'weight': 0.21450066449073515}];

nodes = {'lexing xie': {'name': 'lexing xie', 'weight': 0}, 'shihfu chang': {'name': 'shihfu chang', 'weight': 0.46041874841469516}, 'changsheng xu': {'name': 'changsheng xu', 'weight': 0.96614954330214442}, 'milind r naphade': {'name': 'milind r naphade', 'weight': 0.17698831947003679}, 'david m blei': {'name': 'david m blei', 'weight': 0.0}, 'qi tian': {'name': 'qi tian', 'weight': 0.78511086317380496}, 'michael i jordan': {'name': 'michael i jordan', 'weight': 0.0085985101834282762},
'john r smith': {'name': 'john r smith', 'weight': 0.44204182117414786}, 'l r rabiner': {'name': 'l r rabiner', 'weight': 0.023461331093153182}, 'apostol natsev': {'name': 'apostol natsev', 'weight': 0.4001017013231325}, 'jon kleinberg': {'name': 'jon kleinberg', 'weight': 0.033761311519733106}, 'lyndon kennedy': {'name': 'lyndon kennedy', 'weight': 0.43208927298527761}, 'chongwah ngo': {'name': 'chongwah ngo', 'weight': 0.90667592812107534},
'david lowe': {'name': 'david lowe', 'weight': 0.04206619679658602}, 'xiansheng hua': {'name': 'xiansheng hua', 'weight': 0.59036560874751487}, 'george a miller': {'name': 'george a miller', 'weight': 0.055942223496586119}, 'ajay divakaran': {'name': 'ajay divakaran', 'weight': 0.57826926655472533}, 'cees g m snoek': {'name': 'cees g m snoek', 'weight': 0.59342571237102515}, 'rong yan': {'name': 'rong yan', 'weight': 0.49123680620975285}, 'wen gao': {'name': 'wen gao', 'weight': 1.0},
'jure leskovec': {'name': 'jure leskovec', 'weight': 0.30063313593645313}, 'thomas hofmann': {'name': 'thomas hofmann', 'weight': 0.07078054539443801}, 'thorsten joachims': {'name': 'thorsten joachims', 'weight': 0.07078054539443801}, 'alexander g hauptmann': {'name': 'alexander g hauptmann', 'weight': 0.50955437298250861}, 'vladimir vapnik': {'name': 'vladimir vapnik', 'weight': 0.074405603688817712}, 'hari sundaram': {'name': 'hari sundaram', 'weight': 0.48546139523485443}};

links2 = [{'source': 'lexing xie', 'target': 'ACM', 'type': 'in', 'weight': 1.0}, {'source': 'lexing xie', 'target': 'changsheng xu', 'type': 'in', 'weight': 0.82022471910112404}, {'source': 'lexing xie', 'target': 'milind r naphade', 'type': 'in', 'weight': 0.033707865168539346},{'source': 'lexing xie', 'target': 'qi tian', 'type': 'in', 'weight': 0.68539325842696608},
{'source': 'lexing xie', 'target': 'test', 'type': 'in', 'weight': 0.30337078651685412}, {'source': 'lexing xie', 'target': 'l r rabiner', 'type': 'in', 'weight': 0.0}, {'source': 'lexing xie', 'target': 'apostol natsev', 'type': 'in', 'weight': 0.19101123595505648}, {'source': 'lexing xie', 'target': 'test4', 'type': 'in', 'weight': 0.0},
{'source': 'lexing xie', 'target': 'test2', 'type': 'in', 'weight': 0.23595505617977541}, {'source': 'lexing xie', 'target': 'chongwah ngo', 'type': 'in', 'weight': 0.50561797752808946},{'source': 'lexing xie', 'target': 'test3', 'type': 'in', 'weight': 0.46067415730337069}, {'source': 'lexing xie', 'target': 'george a miller', 'type': 'in', 'weight': 0.0},
{'source': 'lexing xie', 'target': 'ajay divakaran', 'type': 'in', 'weight': 0.43820224719101164}, {'source': 'lexing xie', 'target': 'cees g m snoek', 'type': 'in', 'weight': 0.43820224719101092}, {'source': 'lexing xie', 'target': 'rong yan', 'type': 'in', 'weight': 0.3033707865168544},{'source': 'lexing xie', 'target': 'jure leskovec', 'type': 'in', 'weight': 0.056179775280898937},
{'source': 'lexing xie', 'target': 'alexander g hauptmann', 'type': 'in', 'weight': 0.32584269662921361},{'source': 'lexing xie', 'target': 'hari sundaram', 'type': 'in', 'weight': 0.25842696629213491},
{'source': 'ACM', 'target': 'lexing xie', 'type': 'out', 'weight': 1.0}, {'source': 'changsheng xu', 'target': 'lexing xie', 'type': 'out', 'weight': 0.0098375180125362116}, {'source': 'milind r naphade', 'target': 'lexing xie', 'type': 'out', 'weight': 0.39831254996410154},{'source': 'qi tian', 'target': 'lexing xie', 'type': 'out', 'weight': 0.049187590062681037},
{'source': 'test', 'target': 'lexing xie', 'type': 'out', 'weight': 0.35475658253178655}, {'source': 'l r rabiner', 'target': 'lexing xie', 'type': 'out', 'weight': 0.32720440346044355}, {'source': 'apostol natsev', 'target': 'lexing xie', 'type': 'out', 'weight': 0.31522829457561652}, {'source': 'test4', 'target': 'lexing xie', 'type': 'out', 'weight': 0.30154131299295778}, {'source': 'test2', 'target': 'lexing xie', 'type': 'out', 'weight': 0.30018178022414466},
{'source': 'chongwah ngo', 'target': 'lexing xie', 'type': 'out', 'weight': 0.0096236589253071644},{'source': 'test3', 'target': 'lexing xie', 'type': 'out', 'weight': 0.16467149716636698}, {'source': 'george a miller', 'target': 'lexing xie', 'type': 'out', 'weight': 0.25278144110473477}, {'source': 'ajay divakaran', 'target': 'lexing xie', 'type': 'out', 'weight': 0.17258428339384174}, {'source': 'cees g m snoek', 'target': 'lexing xie', 'type': 'out', 'weight': 0.15269538828154047}, {'source': 'rong yan', 'target': 'lexing xie', 'type': 'out', 'weight': 0.24000822107659986},{'source': 'jure leskovec', 'target': 'lexing xie', 'type': 'out', 'weight': 0.2258351961138749},
{'source': 'alexander g hauptmann', 'target': 'lexing xie', 'type': 'out', 'weight': 0.22257870546743252},
{'source': 'hari sundaram', 'target': 'lexing xie', 'type': 'out', 'weight': 0.21450066449073515}];

nodes2 = {'lexing xie': {'name': 'lexing xie', 'weight': 0}, 'ACM': {'name': 'ACM', 'weight': 0.46041874841469516}, 'changsheng xu': {'name': 'changsheng xu', 'weight': 0.96614954330214442}, 'milind r naphade': {'name': 'milind r naphade', 'weight': 0.17698831947003679},'qi tian': {'name': 'qi tian', 'weight': 0.78511086317380496},
'test': {'name': 'test', 'weight': 0.44204182117414786}, 'l r rabiner': {'name': 'l r rabiner', 'weight': 0.023461331093153182}, 'apostol natsev': {'name': 'apostol natsev', 'weight': 0.4001017013231325}, 'test4': {'name': 'test4', 'weight': 0.033761311519733106}, 'test2': {'name': 'test2', 'weight': 0.43208927298527761}, 'chongwah ngo': {'name': 'chongwah ngo', 'weight': 0.90667592812107534},
'test3': {'name': 'test3', 'weight': 0.59036560874751487}, 'george a miller': {'name': 'george a miller', 'weight': 0.055942223496586119}, 'ajay divakaran': {'name': 'ajay divakaran', 'weight': 0.57826926655472533}, 'cees g m snoek': {'name': 'cees g m snoek', 'weight': 0.59342571237102515}, 'rong yan': {'name': 'rong yan', 'weight': 0.49123680620975285},
'jure leskovec': {'name': 'jure leskovec', 'weight': 0.30063313593645313},'alexander g hauptmann': {'name': 'alexander g hauptmann', 'weight': 0.50955437298250861},'hari sundaram': {'name': 'hari sundaram', 'weight': 0.48546139523485443}};


def processdata(gtype, nodes, links):
    snodes = sorted(nodes.values(), key=itemgetter("weight"))
    nodekeys = [v["name"] for v in snodes]
    anglelist = np.linspace(np.pi, 0., num=len(nodekeys)-1)
    x_pos = [0]; x_pos.extend(list(np.cos(anglelist)))
    y_pos = [0]; y_pos.extend(list(np.sin(anglelist)))
    nodedata = { k["name"]:{
            "name": k["name"],
            "weight": k["weight"],
            "id": i,
            "gtype": gtype,
            "size": random(),
            "xpos": x_pos[i],
            "ypos": y_pos[i]
        } for i, k in zip(range(0, len(snodes)), snodes)}
    linkdata = [{
            "source": nodekeys.index(v["source"]),
            "target": nodekeys.index(v["target"]),
            "padding": nodedata[v["target"]]["size"],
            "id": nodedata[v["target"]]["id"] if v["type"] == "in" else nodedata[v["source"]]["id"],
            "gtype": gtype,
            "type": v["type"],
            "weight": v["weight"]
        } for v in links]
    chartdata = [{
            "id": nodedata[v["target"]]["id"] if v["type"] == "in" else nodedata[v["source"]]["id"],
            "name": v["target"] if v["type"] == "in" else v["source"],
            "type": v["type"],
            "gtype": gtype,
            "sum": nodedata[v["target"]]["weight"] if v["type"] == "in" else nodedata[v["source"]]["weight"],
            "weight": v["weight"]
        } for v in links]
    chartdata = sorted(chartdata, key=itemgetter("sum"))
    return { "nodes": list(nodedata.values()), "links": linkdata, "bars": chartdata }


def test(request):
    data1 = processdata("author", nodes, links)
    data2 = processdata("conf", nodes2, links2)
    data3 = processdata("inst", nodes2, links2)
    return render(request, "graph.html", {"author": data1, "conf": data2, "inst": data3})
