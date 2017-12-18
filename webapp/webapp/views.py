import os, sys
from django.shortcuts import render

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON_DIR = os.path.join(os.path.dirname(BASE_DIR), 'python')
sys.path.insert(0, PYTHON_DIR)

from flower_bloomer import getFlower
from mkAff import getAuthor

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
    global keyword
    keyword = ""
    option = optionlist[0] # default selection
    inflflower = None
    authors = []

    # get user input from main.html page
    if request.method == "GET":
        print(request.GET)
        if "search" in request.GET:
            global aid_pid_dict
            keyword = request.GET.get("keyword")
            if keyword != "":
                authors, aid_pid_dict =  getAuthor(keyword) #(authors_testing, dict()) # getAuthor(keyword)
                print(keyword, option, aid_pid_dict)
            option = [x for x in optionlist if x.get('id', '') == request.GET.get("option")][0]

            # path to the influence flowers
            inflin = os.path.join(BASE_DIR, "output/flower1.png")
            inflby = os.path.join(BASE_DIR, "output/flower2.png")
            inflflower = []#[inflin, inflby]
        if "submit" in request.GET:
            print(type(request.GET.get("authorlist")))
            authorIDs = request.GET.getlist("authorlist")
            print("\n\n\n{}\n\n\n\n\n\n{}\n\n\n\n\n\n\n\n\n".format(authorIDs, aid_pid_dict))
            papers = []
            for aid in authorIDs:
                papers.extend(aid_pid_dict[aid])
            inflflower = getFlower(papers, keyword)
            print("authorIDs: "+str(authorIDs))

    # render page with data
    return render(request, "main.html", {
        "autoCompleteAuthor": loadAuthorList(),
        "optionlist": optionlist,
        "selectedKeyword": keyword,
        "selectedOption": option,
        "inflflower": inflflower,
        "authors": authors
    })
