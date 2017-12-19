import os, sys
from django.shortcuts import render

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON_DIR = os.path.join(os.path.dirname(BASE_DIR), 'python')
sys.path.insert(0, PYTHON_DIR)

from flower_bloomer import getFlower
from mkAff import getAuthor, getJournal, getConf

entity_of_interest = {'author': getAuthor, 'conf': getConf}

AuthorList = []
def loadAuthorList():
    global AuthorList
    path = os.path.join(BASE_DIR, "webapp/cache/AuthorList.txt")
    if len(AuthorList) == 0:
        with open(path, "r") as f:
            AuthorList = [name.strip() for name in f]
    AuthorList = list(set(AuthorList))
    return AuthorList

def getFlowerTest(aids):
    inflin = os.path.join(BASE_DIR, "output/flower1.png")
    inflby = os.path.join(BASE_DIR, "output/flower2.png")
    inflflower = [inflin, inflby]
    return inflflower

def main(request):
    optionlist = [  # option list
        {"id":"author", "name":"Author"},
        {"id":"conf", "name":"Conf/Journal"},
        {"id":"inst", "name":"Institution"},
    ]
    global keyword, option
    keyword = ""
    option = optionlist[0] # default selection
    inflflower = None
    entities = []

    # get user input from main.html page
    if request.method == "GET":
        print(request.GET)
        if "search" in request.GET:
            global id_pid_dict
            keyword = request.GET.get("keyword")
            option = [x for x in optionlist if x.get('id', '') == request.GET.get("option")][0]
            if keyword != "":
                entities, id_pid_dict =  entity_of_interest[option['id']](keyword) #(authors_testing, dict()) # getAuthor(keyword)

            # path to the influence flowers
            inflin = os.path.join(BASE_DIR, "output/flower1.png")
            inflby = os.path.join(BASE_DIR, "output/flower2.png")
            if option.get('id') == 'conf':
                print("executed if statement" + " if option['id'] == 'conf':")
                inflflower = getFlower(id_2_paper_id=id_pid_dict, name=keyword, ent_type='conf')
            else:
                inflflower = []#[inflin, inflby]
        if "submit" in request.GET:
            selected_ids = request.GET.getlist("authorlist")
            id_2_paper_id = dict()
            for aid in selected_ids:
                id_2_paper_id[aid] = id_pid_dict[aid]
            inflflower = getFlower(id_2_paper_id=id_2_paper_id, name=keyword, ent_type='author')

    # render page with data
    return render(request, "main.html", {
        "autoCompleteAuthor": loadAuthorList(),
        "optionlist": optionlist,
        "selectedKeyword": keyword,
        "selectedOption": option,
        "inflflower": inflflower,
        "authors": entities
    })
