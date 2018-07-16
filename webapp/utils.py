import os
from webapp.elastic import query_cache_paper_info, query_author_group, query_paper_group
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


def printNested(obj, indent=0):
    if type(obj) in [list,tuple,set]:
        for elem in obj:
            printNested(elem, indent)
    elif type(obj) is dict:
        for key, value in obj.items():
            print((indent*"\t")+str(key)+":")
            printNested(value,indent+1)
    else:
        print(indent*"\t"+str(obj))


def printDict(d, nested=False):
    if not nested:
        for k,v in d.items():
            print('k: {}\tv: {}'.format(k,v))
    else:
        printNested(d, 0)


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
    cachetype = query.get("type")
    document_id = query.get("id")
    print(document_id)
    if cachetype == query_type[0]:
        aid = query.get("id")
        aname = query.get("name").replace("_", " ")
        data["papers"] = query_cache_paper_info(aid)
        data["names"] = [aname]
        data["flower_name"] = aname
        return data, "author", aname
    elif cachetype == query_type[1]:
        gname = query.get('name').replace("_", " ")
        data["papers"] = query_author_group(gname)
        data["names"] = [gname]
        data["flower_name"] = gname
        return data, "author", gname
    elif cachetype == query_type[2]:
        pname = query.get("name")
        data["papers"] = query_paper_group(document_id)
        data["names"] = [pname]
        data["flower_name"] = pname
        return data, "author", pname 
