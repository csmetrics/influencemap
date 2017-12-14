import os, sys
from django.shortcuts import render

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON_DIR = os.path.join(os.path.dirname(BASE_DIR), 'python')
sys.path.insert(0, PYTHON_DIR)

from mkAff import getAuthors 

def main(request):
    optionlist = [  # option list
        {"id":"author", "name":"Author"},
        {"id":"conf", "name":"Conf/Journal"},
        {"id":"inst", "name":"Institution"},
    ]
    keyword = ""
    option = optionlist[0] # default selection
    inflflower = None
    authors = []

    # get user input from main.html page
    if request.method == "POST":
        keyword = request.POST.get("keyword")
        if keyword != "":
            authors =  getAuthors(keyword)
        option = [x for x in optionlist if x.get('id', '') == request.POST.get("option")][0]
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
