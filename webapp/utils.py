import os, json
from core.search.elastic import *
from core.flower.high_level_get_flower import default_config

import matplotlib.pylab as plt
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# option list for radios
optionlist = [  # option list
    {"id":"author", "name":"Author"},
    {"id":"conference", "name":"Conference"},
    {"id":"journal", "name":"Journal"},
    {"id":"institution", "name":"Institution"},
    {"id":"paper", "name": "Paper"}]

# initialise as no autocomplete lists yet (wait until needed)
autoCompleteLists = {}

def read_gallery_group(filename):
    if not os.path.exists(filename):
        return []
    else:
        group_list = json.load(open(filename, "r"))
        return sorted(group_list, key=lambda x: (x["Year"], x["DisplayName"]) if ("Year" in x) else (0, x["DisplayName"]))


def load_gallery():
    with open("webapp/static/gallery/browse_list.json", "r") as fh:
        browse_list = json.load(fh)
    for group in browse_list:
        for subgroup in group["subgroups"]:
            if subgroup["type"] == "inner":
                group_file = "webapp/static/gallery/{}.json".format(subgroup["tag"])
                subgroup["docs"] = read_gallery_group(group_file)
            else: # subgroup["type"] == "outer":
                for subsubgroup in subgroup["subgroups"]:
                    if subsubgroup["type"] == "inner":
                        group_file = "webapp/static/gallery/{}.json".format(subsubgroup["tag"])
                        subsubgroup["docs"] = read_gallery_group(group_file)
    return browse_list

def loadList(entity):
    path = os.path.join(BASE_DIR, "webapp/cache/"+entity+"List.txt")
    if entity == 'paper':
        return []
    elif entity not in autoCompleteLists.keys():
        with open(path, "r") as f:
            autoCompleteLists[entity] = [name.strip() for name in f]
        autoCompleteLists[entity] = list(set(autoCompleteLists[entity]))
    return autoCompleteLists[entity]

def get_navbar_option(keyword = "", option = ""):
    return {
        "optionlist": optionlist,
        "selectedKeyword": keyword,
        "selectedOption": [opt for opt in optionlist if opt['id'] == option][0] if option != "" else optionlist[0],
    }

def get_url_query(query):
    config = None
    if "pmin" in query:
        config = {
            "pub_lower": int(query.get("pmin")),
            "pub_upper": int(query.get("pmax")),
            "cit_lower": int(query.get("cmin")),
            "cit_upper": int(query.get("cmax")),
            "self_cite": query.get("selfcite") == "true",
            "icoauthor": query.get("coauthor") == "true",
            "num_leaves": int(query.get("node")),
            "order": query.get("order"),
            "cmp_ref": query.get("cmp_ref") == "true",
        }

    document_id = query.get("id")
    document = query_browse_group(document_id)
    return document, "author", config

def add_author_order(paper_info):
    '''
    '''
    author_order = author_order_query(paper_info['PaperId'])

    for author in paper_info['Authors']:
        if author['AuthorId'] not in author_order:
            continue
        author['AuthorOrder'] = author_order[author['AuthorId']]

    return paper_info
