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

# initialise as no saved pids
saved_pids = dict() 

# initialise as no expanded ids
expanded_ids = dict()

# initialise as no autocomplete lists yet (wait until needed)
autoCompleteLists = {}

# dictionary to store option specific functions
dataFunctionDict = {
    'get_ids':{
        'author': getAuthor,
        'conference': getConf,
        'institution': getAff,
        'journal': getJournal},
    'get_pids':{
        'conference': getConfPID,
        'jounral': getJourPID,
        'institution': getAffPID}}

# option list for radios
optionlist = [  # option list
        {"id":"author", "name":"Author"},
        {"id":"conference", "name":"Conference"},
        {"id":"journal", "name":"Journal"},
        {"id":"institution", "name":"Institution"}]


def loadList(entity):
    path = os.path.join(BASE_DIR, "webapp/cache/"+entity+"List.txt")
    if entity not in autoCompleteLists.keys():
        with open(path, "r") as f:
            autoCompleteLists[entity] = [name.strip() for name in f]
        autoCompleteLists[entity] = list(set(autoCompleteLists[entity]))
    return autoCompleteLists[entity]

def autocomplete(request):
    entity_type = request.GET.get('option')
    data = loadList(entity_type)
    return JsonResponse(data,safe=False)


@csrf_exempt
def search(request):
    global saved_pids, expanded_ids
    print("search!!", request.GET)

    entities = []

    keyword = request.GET.get("keyword")
    option = request.GET.get("option")
    expand = True if request.GET.get("expand") == 'true' else False

    if keyword not in expanded_ids.keys():
        expanded_ids[keyword] = list()

    if keyword:
        if option == 'author':
            try:
                entities, saved_pids[keyword], expanded_ids[keyword] = getAuthor(keyword, progressCallback, nonExpandAID=expanded_ids[keyword], expand=expand)
            except:
                entities_and_saved_pids = getAuthor(keyword, progressCallback, nonExpandAID=expanded_ids[keyword], expand=expand)
                entities = entities_and_saved_pids[0]
                saved_pids[keyword] = {**entities_and_saved_pids[1], **saved_pids[keyword]}
        else:
            entities = dataFunctionDict['get_ids'][option](keyword, progressCallback)

    data = {"entities": entities,}

    return JsonResponse(data, safe=False)



def submit(request):
    global option, saved_pids

    selected_ids = request.GET.get("authorlist").split(",")
    option = request.GET.get("option")
    keyword = request.GET.get('keyword')
    selfcite = True if request.GET.get("selfcite") == "true" else False

    if option in ['conference', 'journal']:
        id_pid_dict = dataFunctionDict['get_pids'][option](selected_ids)
    elif option in ['institution']:
        selected_names = request.GET.get("nameslist").split(",")
        id_pid_dict = dataFunctionDict['get_pids'][option](selected_ids, selected_names)
    elif option in ['author']:
        id_pid_dict = saved_pids[keyword]
    else:
        print("option: {}. This is not a valid selection".format(option))
        id_pid_dict = None

    id_2_paper_id = dict()

    for aid in selected_ids:
        id_2_paper_id[aid] = id_pid_dict[aid]

    image_names = getFlower(id_2_paper_id=id_2_paper_id, name=keyword, ent_type=option)

    image_urls = ["static/" + url for url in image_names]

    data = {"images": image_urls,}
    return JsonResponse(test, safe=False)


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
