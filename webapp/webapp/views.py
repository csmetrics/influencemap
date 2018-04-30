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

import entity_type as ent
from parse_academic_search import parse_search_results
from academic_search import *
from draw_flower_test import draw_flower
from flower_bloomer import getFlower, getPreFlowerData
from mkAff import getAuthor, getJournal, getConf, getAff, getConfPID, getJourPID, getConfPID, getAffPID
from mag_flower_bloom import *


from get_entity import entity_from_name
from influence_df import get_filtered_influence
from score_influence import score_entities

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
	{"id":"institution", "name":"Institution"},
    {"id":"paper", "name": "Paper"}]


str_to_ent = {
	"author": ent.Entity_type.AUTH,
	"conference": ent.Entity_type.CONF,
	"journal": ent.Entity_type.JOUR,
	"institution": ent.Entity_type.AFFI
    }


# flower_types
flower_leaves = { 'author': [ent.Entity_type.AUTH]
                , 'conf': [ent.Entity_type.CONF, ent.Entity_type.JOUR]
                , 'inst': [ent.Entity_type.AFFI]
                }

def printDict(d):
    for k,v in d.items():
        print('k: {}\tv: {}'.format(k,v))


def loadList(entity):
    path = os.path.join(BASE_DIR, "webapp/cache/"+entity+"List.txt")
    if entity == 'paper':
        return []
    elif entity not in autoCompleteLists.keys():
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
    return render(request, "main.html")

@csrf_exempt
def browse(request):

    browse_list_filename = '/localdata3/common/browse_lists.json'
    with open(browse_list_filename, 'r') as fp:
        browse_list = json.load(fp)

    data = {'list': browse_list}

    return render(request, "browse.html", data)


@csrf_exempt
def create(request):
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
    return render(request, "create.html", {
	"navbarOption": {
	    "optionlist": optionlist,
	    "selectedKeyword": keyword,
	    "selectedOption": option,
	},
        "search": search
    })

s = {
    'author': ('<h5>{name}</h5><p>{affiliation}, Papers: {paperCount}, Citations: {citations}</p></div>'),
         # '<div style="float: left; width: 50%; padding: 0;"><p>Papers: {paperCount}</p></div>'
         # '<div style="float: right; width: 50%; text-align: right; padding: 0;"<p>Citations: {citations}</p></div>'),
    'conference': ('<h5>{name}</h5>'
        '<div style="float: left; width: 50%; padding: 0;"><p>Papers: {paperCount}</p></div>'
        '<div style="float: right; width: 50%; text-align: right; padding: 0;"<p>Citations: {citations}</p></div>'),
    'institution': ('<h5>{name}</h5>'
        '<div style="float: left; width: 50%; padding: 0;"><p>Papers: {paperCount}</p></div>'
        '<div style="float: right; width: 50%; text-align: right; padding: 0;"<p>Citations: {citations}</p></div>'),
    'journal': ('<h5>{name}</h5>'
        '<div style="float: left; width: 50%; padding: 0;"><p>Papers: {paperCount}</p></div>'
        '<div style="float: right; width: 50%; text-align: right; padding: 0;"<p>Citations: {citations}</p></div>'),
    'paper': ('<h5>{title}</h5>'
        '<div><p>Citations: {citations}</p></div>')
}

@csrf_exempt
def search(request):
    keyword = request.POST.get("keyword")
    entityType = request.POST.get("option")
    data = get_entities_from_search(keyword, entityType)

    for i in range(len(data)):
        # print(entity)
        entity = {'data': data[i]}
        entity['display-info'] = s[entityType].format(**entity['data'])
        entity['table-id'] = "{}_{}".format(entity['data']['entity-type'], entity['data']['eid'])
        data[i] = entity
        # print(entity)
    print(data[0])
    return JsonResponse({'entities': data}, safe=False)


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

    data = json.loads(request.POST.get('data'))

    option = data.get("option")
    keyword = data.get('keyword')
    selfcite = data.get("selfcite") 
    min_year = int(data.get("bot_year_min"))
    max_year = int(data.get("top_year_max"))

    selection = list(data.get("selection").values())
    print("submit")

    # Default Dates need fixing
    min_year = None
    max_year = None

    # USER NEEDS TO SELECT ENTITIES FIRST
    #entity_list_init = entity_from_name(keyword, entity_type)
    entity_list_init = list()
    for row in selection:
        print(row['name'])
        entity_list_init.append(ent.Entity(row['name'], row['eid'], str_to_ent[row['entity-type']]))


    print(entity_list_init)
    #entity_type = data.get('entity_type')
    #entity_names = data.get('entity_names')

    entity_list = list()
    for entity in entity_list_init:
        # Need to render and allow user selection here
        print(entity.entity_id, entity.get_papers())
        if entity.get_papers() is not None:
            entity_list.append(entity)
        # User returns a reduced filtered entity list
        # Futher returns a filter to select papers for each of the entities'
        # papers

        # entity_list = data.get('entity_list')
        # filters = data.get('filter')
    #print(entity_list)

    filters = dict()
    filtered_entity_list = entity_list

    influence_df = get_filtered_influence(filtered_entity_list, filters)

    # Get the entity names
    entity_names = list(map(lambda x: x.entity_name, filtered_entity_list))
    entity_names.append('')
    print(entity_names)

    cache_score = [None, None, None]
    flower_score = [None, None, None]

    for i, flower_item in enumerate(flower_leaves.items()):
        name, leaf = flower_item

        entity_score_cache = score_entities(influence_df, leaf)

        entity_score = entity_score_cache[~entity_score_cache['entity_id'].str.lower().isin(
                                          entity_names)]
        print(entity_score)

        agg_score = agg_score_df(entity_score, min_year, max_year)
        agg_score.ego = entity_names[0]

        score = score_df_to_graph(agg_score)

        cache_score[i] = entity_score_cache
        flower_score[i] = score

    data1 = processdata("author", flower_score[0])
    data2 = processdata("conf", flower_score[1])
    data3 = processdata("inst", flower_score[2])

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
            "range": [min_year, max_year] # placeholder value, just for testing
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

