import os, sys
import base64
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from .utils import progressCallback

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON_DIR = os.path.join(os.path.dirname(BASE_DIR), 'python')
sys.path.insert(0, PYTHON_DIR)

from flower_bloomer import getFlower
from mkAff import getAuthor, getJournal, getConf, getAff, getConfPID, getJourPID, getConfPID, getAffPID



autoCompleteLists = {}
optionlist = [  # option list
    {"id":"author", "name":"Author"},
    {"id":"conference", "name":"Conference"},
    {"id":"journal", "name":"Journal"},
    {"id":"institution", "name":"Institution"}
]

def loadList(entity):
    path = os.path.join(BASE_DIR, "webapp/cache/"+entity+"List.txt")
    if entity not in autoCompleteLists.keys():
        with open(path, "r") as f:
            autoCompleteLists[entity] = [name.strip() for name in f]
        autoCompleteLists[entity] = list(set(autoCompleteLists[entity]))
    return autoCompleteLists[entity]


dataFunctionDict = {
    'get_ids':{
        'author': getAuthor,
        'conference': getConf,
        'institution': getAff,
        'journal': getJournal
    },
    'get_pids':{
        'conference': getConfPID,
        'jounral': getJourPID,
        'institution': getAffPID
    }
}

def autocomplete(request):
    entity_type = request.GET.get('option')
    print(request)
    print(request.GET.get('option'))
    data = loadList(entity_type)
    return JsonResponse(data,safe=False)


selfcite = False
expanded_ids = []

@csrf_exempt
def search(request):
    global keyword, optionlist, option, selfcite, author_id_pid_dict, expanded_ids
    print("search!!", request.GET)
    inflflower = None
    entities = []

    selfcite = True if request.GET.get("selfcite") == "true" else False
    keyword = request.GET.get("keyword")
    option = request.GET.get("option")
    expand = True if request.GET.get("expand") == 'true' else False
    if not expanded_ids:
        expanded_ids = []

    print(keyword)

    if keyword:
        if option == 'author':
            try:
                entities, author_id_pid_dict, expanded_ids = getAuthor(keyword, progressCallback, nonExpandAID=expanded_ids, expand=expand)
            except:
                entities, author_id_pid_dict = getAuthor(keyword, progressCallback, nonExpandAID=expanded_ids, expand=expand)
        else:
            entities = dataFunctionDict['get_ids'][option](keyword, progressCallback)

    data = {"entities": entities,}

    return JsonResponse(data, safe=False)



def submit(request):
    global keyword, option, selfcite, author_id_pid_dict

    selected_ids = request.GET.get("authorlist").split(",")
    option = request.GET.get("option")

    if option in ['conference', 'journal']:
        id_pid_dict = dataFunctionDict['get_pids'][option](selected_ids)
    elif option in ['institution']:
        selected_names = request.GET.get("nameslist").split(",")
        id_pid_dict = dataFunctionDict['get_pids'][option](selected_ids, selected_names)
    elif option in ['author']:
        id_pid_dict = author_id_pid_dict
    else:
        print("option: {}. This is not a valid selection".format(option))
        id_pid_dict = None

    id_2_paper_id = dict()

    for aid in selected_ids:
        id_2_paper_id[aid] = id_pid_dict[aid]

    image_names = getFlower(id_2_paper_id=id_2_paper_id, name=keyword, ent_type=option)
    image_urls = ["static/" + url for url in image_names]

    data = {
        "images": image_urls,
        "navbarOption": {
            "optionlist": optionlist,
            "selectedKeyword": keyword,
            "selectedOption": [o for o in optionlist if o["id"] == option][0],
        }
    }
    return render(request, "flower.html", data)


def main(request):
    global keyword, optionlist, option, selfcite
    keyword = ""
    option = optionlist[0] # default selection

    # render page with data
    return render(request, "main.html", {
        "navbarOption": {
            "optionlist": optionlist,
            "selectedKeyword": keyword,
            "selectedOption": option,
        }
    })
