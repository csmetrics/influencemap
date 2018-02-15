import os, sys, json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from .utils import progressCallback, resetProgress
from .graph import processdata


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON_DIR = os.path.join(os.path.dirname(BASE_DIR), 'python')
sys.path.insert(0, PYTHON_DIR)

from flower_bloomer import getFlower, getPreFlowerData
from mkAff import getAuthor, getJournal, getConf, getAff, getConfPID, getJourPID, getConfPID, getAffPID
# initialise as no saved pids
saved_pids = dict()

# initialise as no saved entities
saved_entities = dict()

# initialise as no expanded ids
expanded_ids = dict()

# initialise no stored flower data frames
pre_flower_data_dict = dict()

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
	'journal': getJourPID,
	'institution': getAffPID}}

# option list for radios
optionlist = [  # option list
	{"id":"author", "name":"Author"},
	{"id":"conference", "name":"Conference"},
	{"id":"journal", "name":"Journal"},
	{"id":"institution", "name":"Institution"}]


def printDict(d):
    for k,v in d.items():
        print('k: {}\tv: {}'.format(k,v))


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

selfcite = False
expanded_ids = dict()

@csrf_exempt
def main(request):
    print(request)
 
    try:
        data = json.loads(request.POST.get('data'))
        keyword = data.get('keyword', '')
        search = data.get('search') == 'true'
        option = [opt for opt in optionlist if opt['id'] == data.get('option')][0]
    except:
        keyword = ""
        search = False
        option = optionlist[0] # default selection
    print(search)    
    # render page with data
    return render(request, "main.html", {
	"navbarOption": {
	    "optionlist": optionlist,
	    "selectedKeyword": keyword,
	    "selectedOption": option,
	},
        "search": search
    })


@csrf_exempt
def search(request):
    print(request)
    request.session['id'] = 'id_' + str(datetime.now())
    global saved_pids, expanded_ids
    entities = []

    keyword = request.POST.get("keyword")
    option = request.POST.get("option")
    expand = True if request.POST.get("expand") == 'true' else False
    if keyword not in expanded_ids.keys():
         expanded_ids[keyword] = list()

    if keyword:
        if option == 'author':
            try:
                entities, saved_pids[keyword], expanded_ids[keyword] = getAuthor(keyword, progressCallback, nonExpandAID=expanded_ids[keyword], expand=expand)
                saved_entities[keyword] = entities
            except:
                entities_and_saved_pids = getAuthor(keyword, progressCallback, nonExpandAID=expanded_ids[keyword], expand=expand)
                entities = entities_and_saved_pids[0]
                saved_entities[keyword] += entities
                saved_pids[keyword] = {**entities_and_saved_pids[1], **saved_pids[keyword]}
        else:
            entities = dataFunctionDict['get_ids'][option](keyword, progressCallback)
            saved_entities[keyword] = entities
    data = {"entities": entities,}
    return JsonResponse(data, safe=False)


def view_papers(request):
    print(request)
    resetProgress()
    data = json.loads(request.POST.get('data'))
    selectedIds = data.get('selectedIds').split(',')
    selectedNames = data.get('selectedNames').split(',')
    entityType = data.get('entityType')
    expanded = data.get('expanded') 
    option = data.get('option')
    name = data.get('name')
    if entityType == 'author':
        entities = saved_entities[name]
        paper_dict = saved_pids[name]
        entities = [x for x in entities if x['id'] in selectedIds]
        for entity in entities:
            entity['field'] = ['_'.join([str(y) for y in x]) for x in entity['field']]
    else:
        entities = saved_entities[name]
        get_pid_params = [selectedIds] if entityType != 'institution' else ([{'id':selectedIds[i],'name':selectedNames[i]} for i in range(len(selectedIds))], name)
        paper_dict = dataFunctionDict['get_pids'][entityType](*get_pid_params)
        entities = [x for x in entities if x['id'] in selectedIds]

    simplified_paper_dict = dict()

    for k, v in paper_dict.items(): # based on a dict of type entity(aID, entity_type('auth_id')):[(paperID, affiliationName, paperTitle, year, date, confName)] according to mkAff.py
        eid = k.entity_id
        if eid in selectedIds:
            sorted_papers = sorted(v, key= lambda x: x['year'] if entityType != 'institution' else x['paperID'], reverse = True)
            simplified_paper_dict[eid] = sorted_papers
    data = {
        'entityTuples': entities,
        'papersDict': simplified_paper_dict,
        'entityType': entityType,
        'selectedInfo': selectedIds,
        'keyword': name,
        "navbarOption": {
            "optionlist": optionlist,
            "selectedKeyword": name,
            "selectedOption": [opt for opt in optionlist if opt['id'] == option][0],
        }

    }

    return render(request, 'view_papers.html', data)



@csrf_exempt
def submit(request):
    print(request)
    resetProgress()
    global saved_pids
    data = json.loads(request.POST.get('data'))
    papers_string = data['papers']   # 'eid1:pid,pid,...,pid_entity_eid2:pid,...'
    id_papers_strings = papers_string.split('_entity_')
    id_2_paper_id = dict()

    for id_papers_string in id_papers_strings:
        eid, pids = id_papers_string.split(':')
        id_2_paper_id[eid] = pids.split(',')

    unselected_papers_string = data.get('unselected_papers')   # 'eid1:pid,pid,...,pid_entity_eid2:pid,...'
    unselected_id_papers_strings = unselected_papers_string.split('_entity_')

    unselected_id_2_paper_id = dict()
    if unselected_papers_string != "":
        for us_id_papers_string in unselected_id_papers_strings:
            us_eid, us_pids = us_id_papers_string.split(':')
            unselected_id_2_paper_id[us_eid] = us_pids.split(',')

    option = data.get("option")
    keyword = data.get('keyword')
    selfcite = data.get("selfcite") 
    bot_year_min = int(data.get("bot_year_min"))
    top_year_max = int(data.get("top_year_max"))

    pre_flower_data_dict[request.session['id']] = getPreFlowerData(id_2_paper_id, unselected_id_2_paper_id, ent_type = option, cbfunc=progressCallback)
    flower_data = getFlower(data_df=pre_flower_data_dict[request.session['id']], name=keyword, ent_type=option, cbfunc=progressCallback, inc_self=selfcite)

    data1 = processdata("author", flower_data[0])
    data2 = processdata("conf", flower_data[1])
    data3 = processdata("inst", flower_data[2])

    print(data)
    print(selfcite)
    data = {
        "author": data1,
        "conf": data2,
        "inst": data3,
        "navbarOption": {
            "optionlist": optionlist,
            "selectedKeyword": keyword,
            "selectedOption": option,
        },
        "yearSlider": {
            "title": "Publications range",
            "range": [bot_year_min, top_year_max] # placeholder value, just for testing
        },
        "navbarOption": {
            "optionlist": optionlist,
            "selectedKeyword": keyword,
            "selectedOption": [opt for opt in optionlist if opt['id'] == option][0],
        }

    }
    return render(request, "flower.html", data)

@csrf_exempt
def resubmit(request):
    print(request)
    from_year = int(request.POST.get('from_year'))
    to_year = int(request.POST.get('to_year'))
    option = request.POST.get('option')
    keyword = request.POST.get('keyword')
    pre_flower_data = []
    selfcite = request.POST.get('selfcite') == 'true'

    flower_data = getFlower(data_df=pre_flower_data_dict[request.session['id']], name=keyword, ent_type=option, bot_year=from_year, top_year=to_year, inc_self=selfcite)

    data1 = processdata("author", flower_data[0])
    data2 = processdata("conf", flower_data[1])
    data3 = processdata("inst", flower_data[2])

    data = {
        "author": data1,
        "conf": data2,
        "inst": data3,
        "navbarOption": {
            "optionlist": optionlist,
            "selectedKeyword": keyword,
            "selectedOption": option,
        },
    }
    return JsonResponse(data, safe=False)

