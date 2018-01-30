import os, sys, json
from django.shortcuts import render
from operator import itemgetter
from random import random
import numpy as np
from flower_bloomer import getFlower

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON_DIR = os.path.join(os.path.dirname(BASE_DIR), 'python')
sys.path.insert(0, PYTHON_DIR)

def processdata(gtype, egoG):
    center_node = egoG.graph['ego']

    # Get basic node information from ego graph
    outer_nodes = list(egoG)
    outer_nodes.remove(center_node)
    outer_nodes.sort(key=lambda n : egoG.nodes[n]['ratiow'])

    links = egoG.edges(data=True)
    anglelist = np.linspace(np.pi, 0., num=len(outer_nodes))
    x_pos = [0]; x_pos.extend(list(np.cos(anglelist)))
    y_pos = [0]; y_pos.extend(list(np.sin(anglelist)))
    nodedata = { key:{
            "name": key,
            "weight": egoG.nodes[key]["nratiow"],
            "id": i,
            "gtype": gtype,
            "size": egoG.nodes[key]["sumw"],
            "xpos": x_pos[i],
            "ypos": y_pos[i]
        } for i, key in zip(range(1, len(outer_nodes)+1), outer_nodes)}
    nodedata[center_node] = {
        "name": center_node, "weight": 1,
        "id": 0, "gtype": gtype, "size": 1,
        "xpos": x_pos[0], "ypos": y_pos[0]
    }
    nodekeys = [v["name"] for v in sorted(nodedata.values(), key=itemgetter("id"))]
    linkdata = [{
            "source": nodekeys.index(s),
            "target": nodekeys.index(t),
            "padding": nodedata[t]["size"],
            "id": nodedata[t]["id"] if v["direction"] == "in" else nodedata[s]["id"],
            "gtype": gtype,
            "type": v["direction"],
            "weight": v["nweight"]
        } for s, t, v in links]
    chartdata = [{
            "id": nodedata[t]["id"] if v["direction"] == "in" else nodedata[s]["id"],
            "name": t if v["direction"] == "in" else s,
            "type": v["direction"],
            "gtype": gtype,
            "sum": nodedata[t]["weight"] if v["direction"] == "in" else nodedata[s]["weight"],
            "weight": v["weight"]
        } for s, t, v in links]
    chartdata = sorted(chartdata, key=itemgetter("sum"))
    return { "nodes": list(nodedata.values()), "links": linkdata, "bars": chartdata }


def submit(request):
    global option, saved_pids

    papers_string = request.GET.get('papers')   # 'eid1:pid,pid,...,pid_entity_eid2:pid,...'
    id_papers_strings = papers_string.split('_entity_')

    id_2_paper_id = dict()

    for id_papers_string in id_papers_strings:
        eid, pids = id_papers_string.split(':')
        id_2_paper_id[eid] = pids.split(',')

    option = request.GET.get("option")
    keyword = request.GET.get('keyword')
    selfcite = True if request.GET.get("selfcite") == "true" else False

    flower_data = getFlower(id_2_paper_id=id_2_paper_id, name=keyword, ent_type=option)

    data1 = processdata("author", flower_data[0])
    data2 = processdata("conf", flower_data[1])
    data3 = processdata("inst", flower_data[2])

    data = {
        "author": data1,
        "conf": data2,
        "inst": data3,
        # "navbarOption": {
        #    "optionlist": optionlist,
        #    "selectedKeyword": keyword,
        #    "selectedOption": [o for o in optionlist if o["id"] == option][0],
        # }
    }

    return render(request, "graph.html", data)
