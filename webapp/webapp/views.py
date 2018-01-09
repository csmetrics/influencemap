import os, sys
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON_DIR = os.path.join(os.path.dirname(BASE_DIR), 'python')
sys.path.insert(0, PYTHON_DIR)

#from flower_bloomer import getFlower
from mkAff import getAuthor, getJournal, getConf, getAff

entity_of_interest = {'author': getAuthor, 'conference': getConf, 'institution': getAff, 'journal': getJournal}

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

selfcite = False
optionlist = []

@csrf_exempt
def search(request):
    global keyword, optionlist, option, selfcite
    global id_pid_dict

    print("search!!", request.GET)
    inflflower = None
    entities = []

    selfcite = request.GET.get("selfcite")
    keyword = request.GET.get("keyword")
    option = [x for x in optionlist if x.get('id', '') == request.GET.get("option")][0]
    print(keyword)
    if keyword != "":
        print("{}\t{}\t{}".format(datetime.now(), __file__ , entity_of_interest[option['id']].__name__))
        entities, id_pid_dict =  entity_of_interest[option['id']](keyword) #(authors_testing, dict()) # getAuthor(keyword)

    # path to the influence flowers
    inflin = os.path.join(BASE_DIR, "output/flower1.png")
    inflby = os.path.join(BASE_DIR, "output/flower2.png")
    if False: #option.get('id') == 'conf':
        print("{}\t{}\t{}".format(datetime.now(), __file__ , getFlower.__name__))
        inflflower = getFlower(id_2_paper_id=id_pid_dict, name=keyword, ent_type='conference', self_cite=selfcite)
    else:
        inflflower = []#[inflin, inflby]

    data = {
        "inflflower": inflflower,
        "authors": entities,
    }
    return JsonResponse(data, safe=False)

def submit(request):
    selected_ids = request.GET.getlist("authorlist")
    id_2_paper_id = dict()
    for aid in selected_ids:
        id_2_paper_id[aid] = id_pid_dict[aid]
    print("{}\t{}\t{}".format(datetime.now(), __file__ , getFlower.__name__))
    print("selfcite :" + str(selfcite))
    inflflower = getFlower(id_2_paper_id=id_2_paper_id, name=keyword, ent_type=option['id'], self_cite=selfcite)

    data = {
        "optionlist": optionlist,
        "selectedKeyword": keyword,
        "selectedOption": option,
        "inflflower": inflflower,
        "authors": entities,
        "selfcite": selfcite
    }
    return JsonResponse(data, safe=False)

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
