import os, sys, json, pandas
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from collections import Counter
from operator import itemgetter
from webapp.graph import processdata
from webapp.elastic import search_cache
from webapp.utils import *

import core.utils.entity_type as ent
from core.search.parse_academic_search import parse_search_results
from core.search.academic_search import *
from core.flower.draw_flower_test import draw_flower
from core.flower.flower_bloomer import getFlower, getPreFlowerData
from core.utils.mkAff import getAuthor, getJournal, getConf, getAff, getConfPID, getJourPID, getConfPID, getAffPID
from core.search.mag_flower_bloom import *
from core.utils.get_entity import entity_from_name
from core.search.influence_df import get_filtered_score
from core.search.search import search_name
from graph.save_cache import *
from core.utils.load_tsv import tsv_to_dict

from core.flower.high_level_get_flower import get_flower_data_high_level
from core.flower.high_level_get_flower import gen_flower_data
from core.flower.high_level_get_flower import gen_entity_score

# Imports for submit
from core.search.query_paper   import paper_query
from core.search.query_info    import paper_info_check_query, paper_info_mag_check_multiquery
from core.score.agg_paper_info import score_paper_info_list
from core.score.agg_utils      import get_coauthor_mapping
from core.score.agg_utils      import flag_coauthor
from core.utils.get_stats      import get_stats

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# initialise as no saved pids
saved_pids = dict()

# initialise as no saved entities
saved_entities = dict()

# initialise as no expanded ids
expanded_ids = dict()

# initialise no stored flower data frames
pre_flower_data_dict = dict()

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

    browse_list_filename = os.path.join(BASE_DIR, 'webapp/static/browse_lists.json')
    with open(browse_list_filename, 'r') as fp:
        browse_list = json.load(fp)

    for entity in browse_list:
        res = search_cache(entity["cache_index"], entity["cache_type"])
        entity["names"] = list(set([n["_source"]["DisplayName"] for n in res]))
        entity["entities"] = [n["_source"] for n in res]
        for e in (entity["entities"]):
            if "Keywords" in e:
                e["Keywords"] = ", ".join(e["Keywords"])
            if "AuthorIds" in e:
                e["AuthorIds"] = json.dumps(e["AuthorIds"])

    data = {
        'list': browse_list,
        "navbarOption": get_navbar_option()
    }

    return render(request, "browse.html", data)


@csrf_exempt
def create(request):
    print(request)

    try:
        data = json.loads(request.POST.get('data'))
        keyword = data.get('keyword', '')
        search = data.get('search') == 'true'
        option = data.get('option')
    except:
        keyword = ""
        option = ""
        search = False

    print(search)
    # render page with data
    return render(request, "create.html", {
        "navbarOption": get_navbar_option(keyword, option),
        "search": search
    })



@csrf_exempt
def curate(request):
    print(request)

    try:
        data = json.loads(request.POST.get('data'))
        keyword = data.get('keyword', '')
        search = data.get('search') == 'true'
        option = data.get('option')
    except:
        keyword = ""
        option = ""
        search = False

    print(search)
    # render page with data
    return render(request, "curate.html", {
        "navbarOption": get_navbar_option(keyword, option),
        "search": search
    })


@csrf_exempt
def curate_load_file(request):
    print("this is in the curate_load_file func")
    filename = request.POST.get("filename")
    print("filename: ", filename)
    try:
        data = tsv_to_dict(filename)
        success = "true"
    except FileNotFoundError:
        data = {}
        success = "false"
    return JsonResponse({'data': data, 'success': success}, safe=False)



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
        '<div><p>Citations: {citations}, Field: {fieldOfStudy}</p><p>Authors: {authorName}</p></div>')
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


'''
s = {
    'author': ('<h5>{DisplayName}</h5><p>Papers: {PaperCount}, Citations: {CitationCount}</p></div>'),
         # '<div style="float: left; width: 50%; padding: 0;"><p>Papers: {paperCount}</p></div>'
         # '<div style="float: right; width: 50%; text-align: right; padding: 0;"<p>Citations: {citations}</p></div>'),
    'conference': ('<h5>{DisplayName}</h5>'
        '<div style="float: left; width: 50%; padding: 0;"><p>Papers: {PaperCount}</p></div>'
        '<div style="float: right; width: 50%; text-align: right; padding: 0;"<p>Citations: {CitationCount}</p></div>'),
    'institution': ('<h5>{DisplayName}</h5>'
        '<div style="float: left; width: 50%; padding: 0;"><p>Papers: {PaperCount}</p></div>'
        '<div style="float: right; width: 50%; text-align: right; padding: 0;"<p>Citations: {CitationCount}</p></div>'),
    'journal': ('<h5>{DisplayName}</h5>'
        '<div style="float: left; width: 50%; padding: 0;"><p>Papers: {PaperCount}</p></div>'
        '<div style="float: right; width: 50%; text-align: right; padding: 0;"<p>Citations: {CitationCount}</p></div>'),
    'paper': ('<h5>{PaperTitle}</h5>'
        '<div><p>Citations: {CitationCount}</p></div>')
}

idkeys = {'paper': 'PaperId', 'author': 'AuthorId', 'institution': 'AffiliationId', 'journal': 'JournalId', 'conference': 'ConferenceSeriesId'}

@csrf_exempt
def search(request):
    global idkeys
    keyword = request.POST.get("keyword")
    entity_type = request.POST.get("option")
    data = search_name(keyword, entity_type)
    idkey = idkeys[entity_type]
    for i in range(len(data)):
        # print(entity)
        entity = {'data': data[i]}
        entity['display-info'] = s[entity_type].format(**entity['data'])
        entity['table-id'] = "{}_{}".format(entity_type, entity['data'][idkey])
        data[i] = entity
        # print(entity)
    print(data[0])
    return JsonResponse({'entities': data}, safe=False)
'''

@csrf_exempt
def manualcache(request):
    data = (json.loads(request.POST.get('ent_data')))
    cache_type = request.POST.get('cache_type')
    if cache_type == "authorGroup":
        saveNewAuthorGroupCache(data)
        paper_info_mag_check_multiquery(data['Papers'])
    elif cache_type == "paperGroup":
        saveNewPaperGroupCache(data)
        paper_info_mag_check_multiquery(data['PaperIds'])
    return JsonResponse({},safe=False)

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
        "navbarOption": get_navbar_option(name, option),
    }

    return render(request, 'view_papers.html', data)


@csrf_exempt
def submit(request):

    if request.method == "GET":
        # from url e.g. /submit/?type=author_id&id=2146610949&name=stephen_m_blackburn
        # data should be pre-processed and cached
        data, option, keyword = get_url_query(request.GET)
    else:
        data = json.loads(request.POST.get('data'))
         # normalisedName: <string>   # the normalised name from entity with highest paper count of selected entities
         # entities: {"normalisedName": <string>, "eid": <int>, "entity_type": <author | conference | institution | journal | paper>
        option = data.get("option")   # last searched entity type (confusing for multiple entities)
        keyword = data.get('keyword') # last searched term (doesn't really work for multiple searches)

    # Default Dates
    min_year = None
    max_year = None

    time_cur = datetime.now()

    # Get the selected paper
    selected_papers = data.get('papers')
    entity_names    = data.get('names')
    flower_name     = data.get('flower_name')


    print()
    print('Number of Papers Found: ', len(selected_papers))
    print('Time taken: ', datetime.now() - time_cur)
    print()

    time_cur = datetime.now()

    # Turn selected paper into information dictionary list
    paper_information = paper_info_mag_check_multiquery(selected_papers) # API

    # Get coauthors
    coauthors = get_coauthor_mapping(paper_information)

    print()
    print('Number of Paper Information Found: ', len(paper_information))
    print('Time taken: ', datetime.now() - time_cur)
    print()

    # Get min and maximum year
    years = [info['Year'] for info in paper_information if 'Year' in info]
    min_pub_year, max_pub_year = min(years), max(years)

    # caculate pub/cite chart data
    cont_pub_years = range(min_pub_year, max_pub_year+1)
    cite_years = set()
    for info in paper_information:
        if 'Citations' in info:
            cite_years.update({entity["Year"] for entity in info['Citations'] if "Year" in entity})

    # Add publication years as well
    cite_years.add(min_pub_year)
    cite_years.add(max_pub_year)

    min_cite_year, max_cite_year = min(cite_years), max(cite_years)
    cont_cite_years = range(min(cite_years), max(cite_years)+1)
    pub_chart = [{"year":k,"value":Counter(years)[k] if k in Counter(years) else 0} for k in cont_cite_years]
    citecounter = {k:[] for k in cont_cite_years}
    for info in paper_information:
        if 'Citations' in info:
            for entity in info['Citations']:
                citecounter[info['Year']].append(entity["Year"])

    cite_chart = [{"year":k,"value":[{"year":y,"value":Counter(v)[y]} for y in cont_cite_years]} for k,v in citecounter.items()]

    # Normalised entity names
    entity_names = list(set(entity_names))
    normal_names = list(map(lambda x: x.lower(), entity_names))

    # Generate score for each type of flower
    entity_scores = gen_entity_score(paper_information, entity_names, self_cite=False)

    # Make flower
    data1, data2, data3 = gen_flower_data(entity_scores, flower_name,
                                          coauthors = coauthors)

    data = {
        "author": data1,
        "conf": data2,
        "inst": data3,
        "yearSlider": {
            "title": "Publications range",
            "pubrange": [min_pub_year, max_pub_year, (max_pub_year-min_pub_year+1)],
            "citerange": [min_cite_year, max_cite_year],
            "pubChart": pub_chart,
            "citeChart": cite_chart
        },
        "navbarOption": get_navbar_option(keyword, option)
    }

    # Set cache
    cache = {'cache': selected_papers, 'coauthors': coauthors}

    stats = get_stats(paper_information)
    data['stats'] = stats

    # Cache from flower data
    for key, value in cache.items():
        request.session[key] = value

    request.session['flower_name']  = flower_name
    request.session['entity_names'] = entity_names
    return render(request, "flower.html", data)


@csrf_exempt
def submit_from_browse(request):

    data = json.loads(request.POST.get('data'))

    option = data.get("option")
    keyword = data.get('keyword')
    authorids = data.get('AuthorIds')
    normalizedname = data.get('NormalizedName')

    # Default Dates need fixing
    min_year = None
    max_year = None

    cache, data = get_flower_data_high_level(option, authorids, normalizedname)
    data["navbarOption"] = get_navbar_option(keyword, option)

    # Cache from flower data
    for key, value in cache.items():
        request.session[key] = value

    request.session['flower_name']  = normalizedname
    request.session['entity_names'] = [normalizedname]
    return render(request, "flower.html", data)

@csrf_exempt
def resubmit(request):
    print(request)
    # Get year filter data
    pub_lower = int(request.POST.get('from_pub_year'))
    pub_upper = int(request.POST.get('to_pub_year'))
    cit_lower = int(request.POST.get('from_cit_year'))
    cit_upper = int(request.POST.get('to_cit_year'))


    option = request.POST.get('option')
    keyword = request.POST.get('keyword')
    pre_flower_data = []
    self_cite = request.POST.get('selfcite') == 'true'

    cache        = request.session['cache']
    coauthors    = request.session['coauthors']
    flower_name  = request.session['flower_name']
    entity_names = request.session['entity_names']
    #scores = [pd.read_json(c, orient = 'index') for c in cache]

    # Recompute flowers
    paper_information = paper_info_mag_check_multiquery(cache) # API

    # Generate score for each type of flower
    scores = gen_entity_score(paper_information, entity_names, self_cite=self_cite)

    data1, data2, data3 = gen_flower_data(scores,
                                          flower_name,
                                          pub_lower = pub_lower,
                                          pub_upper = pub_upper,
                                          cit_lower = cit_lower,
                                          cit_upper = cit_upper,
                                          coauthors = coauthors)

    data = {
        "author": data1,
        "conf": data2,
        "inst": data3,
        "navbarOption": get_navbar_option(keyword, option)
    }

    stats = get_stats(paper_information, pub_lower, pub_upper)
    print(stats)
    data['stats'] = stats

    return JsonResponse(data, safe=False)
