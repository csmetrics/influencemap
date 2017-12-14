import os, sys
from django.shortcuts import render

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON_DIR = os.path.join(os.path.dirname(BASE_DIR), 'python')
sys.path.insert(0, PYTHON_DIR)

# from mkAff import getAuthor

def main(request):
    optionlist = [  # option list
        {"id":"author", "name":"Author"},
        {"id":"conf", "name":"Conf/Journal"},
        {"id":"inst", "name":"Institution"},
    ]
    keyword = ""
    option = optionlist[0] # default selection
    inflflower = None
    authors = [
        {"id": 111, "name": "steve", "numpaper": 23, "affiliation":"anu", "field":["f1", "f2"], "mostWeightedPaper":"test", "publishedDate":"2017/8"},
        {"id": 222, "name": "stev2222e", "numpaper": 11, "affiliation":"anu", "field":["f1", "f2"], "mostWeightedPaper":"test", "publishedDate":"2017/8"},
    ]

    # get user input from main.html page
    if request.method == "GET":
        print(request.GET)
        if "search" in request.GET:
            keyword = request.GET.get("keyword")
            # if keyword != "":
            #     authors =  getAuthor(keyword)
            option = [x for x in optionlist if x.get('id', '') == request.GET.get("option")][0]
            print(keyword, option)

            # path to the influence flowers
            inflin = os.path.join(BASE_DIR, "output/flower1.png")
            inflby = os.path.join(BASE_DIR, "output/flower2.png")
            inflflower = []#[inflin, inflby]


    # render page with data
    return render(request, "main.html", {
        "optionlist": optionlist,
        "selectedKeyword": keyword,
        "selectedOption": option,
        "inflflower": inflflower,
        "authors": authors
    })
