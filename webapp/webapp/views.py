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
optionlist = [  # option list
    {"id":"author", "name":"Author"},
    {"id":"conference", "name":"Conference"},
    {"id":"journal", "name":"Journal"},
    {"id":"institution", "name":"Institution"}
]

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


@csrf_exempt
def search(request):
    request.session['id'] = 'id_' + str(datetime.now())
    print('\n\n\n\n\nstart of search: {}\n\n\n\n\n\n'.format(request.session['id']))
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
    print('\n\n\n\n\nend of search: {}\n\n\n\n\n\n'.format(request.session['id']))
    return JsonResponse(data, safe=False)


def view_papers(request):
    print("\n\nrequest: {}\n\n".format(request))
    resetProgress()
    print('\n\n\n\n\nstart of view papers: {}\n\n\n\n\n\n'.format(request.session['id']))
    selectedIds = request.GET.get('selectedIds').split(',')
    selectedNames = request.GET.get('selectedNames').split(',')
    entityType = request.GET.get('entityType')
    expanded = request.GET.get('expanded') == 'true'
    name = request.GET.get('name')
    if entityType == 'author':
#        if expanded:
#            entities, paper_dict = getAuthor(name=name, expand=True, cbfunc=progressCallback, nonExpandAID=expanded_ids[name])
#        else:
#            entities, paper_dict, _ = getAuthor(name=name, expand=False, cbfunc=progressCallback)
        entities = saved_entities[name]
        paper_dict = saved_pids[name]
        entities = [x for x in entities if x['id'] in selectedIds]
        for entity in entities:
            entity['field'] = ['_'.join([str(y) for y in x]) for x in entity['field']]
    else:
#        entities = dataFunctionDict['get_ids'][entityType](name)
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
        'keyword': name
    }

    print('\n\n\n\n\nend of view papers: {}\n\n\n\n\n\n'.format(request.session['id']))
    print('expand {}'.format(expanded))
    return render(request, 'view_papers.html', data)



@csrf_exempt
def submit(request):
    resetProgress()
    print('\n\n\n\n\nstart of submit: {}\n\n\n\n\n\n'.format(request.session['id']))
    global option, saved_pids
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

    print(id_2_paper_id)
    print(unselected_id_2_paper_id)

    option = data.get("option")
    keyword = data.get('keyword')
    selfcite = True if data.get("selfcite") == "true" else False
    bot_year_min = int(data.get("bot_year_min"))
    top_year_max = int(data.get("top_year_max"))


    pre_flower_data_dict[request.session['id']] = getPreFlowerData(id_2_paper_id, unselected_id_2_paper_id, ent_type = option, cbfunc=progressCallback)
    print( pre_flower_data_dict[request.session['id']])    
    flower_data = getFlower(data_df=pre_flower_data_dict[request.session['id']], name=keyword, ent_type=option, cbfunc=progressCallback)

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
        "yearSlider": {
            "title": "Publications range",
            "range": [bot_year_min, top_year_max] # placeholder value, just for testing
        }
    }

    print('\n\n\n\n\nend of submit: {}\n\n\n\n\n\n'.format(request.session['id']))
    return render(request, "flower.html", data)


def resubmit(request):
    from_year = int(request.GET.get('from_year'))
    to_year = int(request.GET.get('to_year'))
    option = request.GET.get('option')
    keyword = request.GET.get('keyword')
    pre_flower_data = []


    print( pre_flower_data_dict[request.session['id']])    
    flower_data = getFlower(data_df=pre_flower_data_dict[request.session['id']], name=keyword, ent_type=option, bot_year=from_year, top_year=to_year)

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
            "selectedOption": [o for o in optionlist if o["id"] == option][0],
        },
    }
    return JsonResponse(data, safe=False)

