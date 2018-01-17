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
from mkAff import getAuthor, getJournal, getConf, getAff, getConfPID, getJourPID, getConfPID




AuthorList = []
ConferenceList = []
JournalList = []
InstitutionList = []
def loadAuthorList():
    global AuthorList
    path = os.path.join(BASE_DIR, "webapp/cache/AuthorList.txt")
    if len(AuthorList) == 0:
        with open(path, "r") as f:
            AuthorList = [name.strip() for name in f]
    AuthorList = list(set(AuthorList))
    return AuthorList

def loadConferenceList():
    global ConferenceList
    path = os.path.join(BASE_DIR, "webapp/cache/ConferenceList.txt")
    if len(ConferenceList) == 0:
        with open(path, "r") as f:
            ConferenceList = [conf.strip() for conf in f]
        ConferenceList = list(set(ConferenceList))
    return ConferenceList

def loadJournalList():
    global JournalList
    path = os.path.join(BASE_DIR, "webapp/cache/JournalList.txt")
    if len(JournalList) == 0:
        with open(path, "r") as f:
            JournalList = [journ.strip() for journ in f]
        JournaList = list(set(JournalList))
    return JournalList

def loadInstitutionList():
    global InstitutionList
    path = os.path.join(BASE_DIR, "webapp/cache/InstitutionList.txt")
    if len(InstitutionList) == 0:
        with open(path, "r") as f:
            InstitutionList = [journ.strip() for journ in f]
        Institutionist = list(set(InstitutionList))
    return InstitutionList


dataFunctionDict = {
    'get_ids':{
        'author': getAuthor,
        'conference': getConf,
        'institution': getAff,
        'journal': getJournal
    },
    'get_pids':{
        'conference': getConfPID,
        'jounral': getJourPID
    },
    'autocomplete':{
        'author': loadAuthorList(),
        'conference': loadConferenceList(),
        'journal': loadJournalList(),
        'institution': loadInstitutionList()
    }
}


def autocomplete(request):
    entity_type = request.GET.get('option')
    print("autocomplete called")
    print(request)
    print(request.GET.get('option'))
    data = dataFunctionDict['autocomplete'][entity_type]
    return JsonResponse(data,safe=False)


selfcite = False
optionlist = []
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
        print("\n\n\nnot yet set up for institutions\n\n\n")
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

    data = {"images": image_urls,}
    return JsonResponse(test, safe=False)


def main(request):
    global keyword, optionlist, option, selfcite
    optionlist = [  # option list
        {"id":"author", "name":"Author", "list": loadAuthorList()},
        {"id":"conference", "name":"Conference", "list": loadConferenceList()},
        {"id":"journal", "name":"Journal", "list": loadJournalList()},
        {"id":"institution", "name":"Institution", "list": loadInstitutionList()}
    ]

    keyword = ""
    option = optionlist[0] # default selection

    # render page with data
    return render(request, "main.html", {
        "optionlist": optionlist,
        "selectedKeyword": keyword,
        "selectedOption": option,
    })


def loadall(request):
    global keyword, optionlist, option, selfcite
    global id_pid_dict

    print("load all!!", request.GET)
    inflflower = None
    entities = []

    selfcite = True if request.GET.get("selfcite") == "true" else False
    keyword = request.GET.get("keyword")
    option = [x for x in optionlist if x.get('id', '') == request.GET.get("option")][0]
    print(keyword)
    if keyword != "":
        print("{}\t{}\t{}".format(datetime.now(), __file__ , entity_of_interest[option['id']].__name__))
        entities, id_pid_dict =  entity_of_interest[option['id']](keyword, progressCallback, expand=True) #(authors_testing, dict()) # getAuthor(keyword)

    data = {
        "authors": entities,
    }

    return JsonResponse(data, safe=False)


