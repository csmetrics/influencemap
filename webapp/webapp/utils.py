import os
from webapp.elastic import query_cache_paper_info, query_author_group
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

def printDict(d):
    for k,v in d.items():
        print('k: {}\tv: {}'.format(k,v))

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
    query_type = [
        "author_id",
        "browse_author_group",
        "browse_paper_group"
    ]
    data = {}
    option = query.get("type")
    if option == query_type[0]:
        aid = query.get("id")
        aname = query.get("name").replace("_", " ")
        data["papers"] = query_cache_paper_info(aid)
        data["names"] = [aname]
        data["flower_name"] = aname
        return data, "author", aname
    elif option == query_type[1]:
        gname = query.get('name').replace("_", " ")
        data["papers"] = query_author_group(gname)
        data["names"] = [gname]
        data["flower_name"] = gname
        return data, "author", gname
