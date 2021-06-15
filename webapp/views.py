import copy
import json
import math
import string
from collections import Counter
from datetime import datetime

import multiprocess
from django.conf import settings
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

import core.utils.entity_type as ent
from core.search.query_info import paper_info_db_check_multiquery
from core.flower.high_level_get_flower import default_config, gen_flower_data
from core.score.agg_paper_info import score_paper_info_list
from core.score.agg_utils import get_coauthor_mapping
from core.search.query_name import (
    get_all_normalised_names, get_conf_journ_display_names)
from core.search.query_paper import get_all_paper_ids
from core.utils.get_stats import get_stats
from core.utils.load_tsv import tsv_to_dict
from graph.save_cache import *
from core.elastic import *
from webapp.graph import ReferenceFlower, compare_flowers
from webapp.shortener import shorten_front, unshorten_url_ext
from webapp.utils import *

from webapp.konigsberg_client import KonigsbergClient

kb_client = KonigsbergClient('http://localhost:8081/get-flower')

BASE_DIR = settings.BASE_DIR

flower_leaves = [ ('author', [ent.Entity_type.AUTH])
                , ('conf'  , [ent.Entity_type.CONF, ent.Entity_type.JOUR])
                , ('inst'  , [ent.Entity_type.AFFI])
                , ('fos'   , [ent.Entity_type.FSTD]) ]

NUM_THREADS = 8
NUM_NODE_INFO = 5

def autocomplete(request):
    entity_type = request.GET.get('option')
    data = loadList(entity_type)
    return JsonResponse(data,safe=False)

@csrf_exempt
def main(request):
    return render(request, "main.html")

@csrf_exempt
def redirect(request):
    return HttpResponseRedirect(unshorten_url_ext(request.get_full_path()))

@csrf_exempt
def browse(request):

    with open("webapp/static/browse_list.json", "r") as fh:
        browse_list = json.load(fh)
    # for b in browse_list:
    #     print(b)
    browse_cache = get_all_browse_cache()
    for group in browse_list:
        for subgroup in group["subgroups"]:
            if subgroup["type"] == "inner":
                #subgroup["document_ids"] = [cache["document_id"] for cache in browse_cache if cache["Type"] == subgroup["tag"]]
                subgroup["docs"] = sorted([cache for cache in browse_cache if cache["Type"] == subgroup["tag"]], key=lambda x: (x["Year"], x["DisplayName"]) if ("Year" in x) else (0, x["DisplayName"]))
            else:
                for subsubgroup in subgroup["subgroups"]:
                    if subsubgroup["type"] == "inner":
                        #subsubgroup["document_ids"] = [cache["document_id"] for cache in browse_cache if cache["Type"] == subsubgroup["tag"]]
                        subsubgroup["docs"] = sorted([cache for cache in browse_cache if cache["Type"] == subsubgroup["tag"]], key=lambda x: (x["Year"], x["DisplayName"]) if ("Year" in x) else (0, x["DisplayName"]))
    browse_cache = {cache["document_id"]: cache for cache in browse_cache}

    return render(request, "browse.html", {"browse_groups": browse_list, "cache_data": browse_cache})

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
    types = get_cache_types()
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
    print(types)
    # render page with data
    return render(request, "curate.html", {
        "navbarOption": get_navbar_option(keyword, option),
        "search": search,
        "types": types
    })

@csrf_exempt
def check_record(request):
    exists, names = check_browse_record_exists(request.POST.get("type"), request.POST.get("name"))
    return JsonResponse({"exists": exists, "names": names})

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
    'author': ('<i class="fa fa-user""></i><h4>{DisplayName}</h4><p>Papers: {PaperCount}, Citations: {CitationCount}</p>'),
    'conference': ('<i class="fa fa-building"></i><h4>{DisplayName}</h4><p>Papers: {PaperCount}, Citations: {CitationCount}</p>'),
    'institution': ('<i class="fa fa-university"></i><h4>{DisplayName}</h4><p>Papers: {PaperCount}, Citations: {CitationCount}</p>'),
    'journal': ('<i class="fa fa-book"></i><h4>{DisplayName}</h4><p>Papers: {PaperCount}, Citations: {CitationCount}</p>'),
    'paper': ('<i class="fa fa-file"></i><h4>{OriginalTitle}</h4><p>Citations: {CitationCount}</p>')
}

@csrf_exempt
def search(request):
    request_data = json.loads(request.POST.get("data"))
    keyword = request_data.get("keyword")
    entityType = request_data.get("option")
    print(entityType, request_data)
    exclude = set(string.punctuation)
    keyword = ''.join(ch for ch in keyword if ch not in exclude)
    keyword = keyword.lower()
    keyword = " ".join(keyword.split())
    id_helper_dict = {"conference": "ConferenceSeriesId", "journal": "JournalId", "institution": "AffiliationId", "paper": "PaperId", "author": "AuthorId"}
    data = []
    if "conference" in entityType:
        data += [(val, "conference") for val in query_conference_series(keyword)]
    if "journal" in entityType:
        data += [(val, "journal") for val in query_journal(keyword)]
    if "institution" in entityType:
        data += [(val, "institution") for val in query_affiliation(keyword)]
    if "paper" in entityType:
        data += [(val, "paper") for val in query_paper(keyword)]
    if "author" in entityType:
        data += [(val, "author") for val in query_author(keyword)]
    for i in range(len(data)):
        entity = {'data': data[i][0]}
        entity['display-info'] = s[data[i][1]].format(**entity['data'])
        if "Affiliation" in entity['data']: entity['display-info'] = entity['display-info'][0:-4] + ", Institution: {}</p>".format(entity['data']["Affiliation"])
        if "Authors" in entity['data']: entity['display-info'] += "<p>Authors: {}</p>".format(", ".join(entity['data']["Authors"]))
        entity['table-id'] = "{}_{}".format(data[i][1], entity['data'][id_helper_dict[data[i][1]]])
        data[i] = entity
    return JsonResponse({'entities': data}, safe=False)


@csrf_exempt
def manualcache(request):
    cache_dictionary = (json.loads(request.POST.get('cache')))
    paper_action = request.POST.get('paperAction')
    saveNewBrowseCache(cache_dictionary)

    if paper_action == "batch":
        paper_ids = get_all_paper_ids(cache_dictionary["EntityIds"])
        addToBatch(paper_ids)
    if paper_action == "cache":
        paper_ids = get_all_paper_ids(cache_dictionary["EntityIds"])
        paper_info_db_check_multiquery(paper_ids)
    return JsonResponse({},safe=False)


def to_flower_dict(data):

    res = []
    for flower_set in zip(*data):
        flower_dict = {
            'author': flower_set[0],
            'conf': flower_set[1],
            'inst': flower_set[2],
            'fos': flower_set[3],
            }

        res.append(flower_dict)

    return res


def as_graph(flower):
    import networkx as nx
    g = nx.DiGraph(ego='ego')
    g.add_node('ego', name='ego', weight=None)
    for i, (id_, score) in enumerate(flower['influencers'].items()):
        g.add_node(id_, nratiow=1, ratiow=1, sumw=1, sum=1, coauthor=False,
                   dif=1, inf_in=0, inf_out=score, bloom_order=i)
        g.add_edge('ego', id_, weight=score, nweight=1, direction='in',
            ratiow=1, dif=1, sumw=1,
            inf_in=score, inf_out=0,
            bloom_order=i)
        g.add_edge(id_, 'ego', weight=0, nweight=1, direction='out',
            ratiow=1, dif=1, sumw=1,
            inf_in=0, inf_out=score,
            bloom_order=i)
    return g


@csrf_exempt
def submit(request):
    session = dict()

    num_leaves = 25 # default
    if request.method == "GET":
        # from url e.g.
        # /submit/?type=author_id&id=2146610949&name=stephen_m_blackburn
        # /submit/?type=browse_author_group&name=lexing_xie
        # data should be pre-processed and cached
        curated_flag = True
        data, option, config = get_url_query(request.GET)
        author_ids = data['EntityIds'].get('AuthorIds', [])
        # selected_papers = get_all_paper_ids(data["EntityIds"])
        entity_names = get_all_normalised_names(data["EntityIds"])
        flower_name = data.get('DisplayName')
    else:
        curated_flag = False
        raise NotImplementedError()

    flower = kb_client.get_flower(author_ids=author_ids)

    from webapp.front_end_helper import make_response_data
    rdata = make_response_data(flower, is_curated=curated_flag)
    # from core.flower.high_level_get_flower import processdata
    # author_flower = processdata(
    #     'author',
    #     as_graph(flower['author_part']),
    #     50,
    #     None,
    #     0)
    # author_flower['total'] = 20


    # rdata = {}
    # rdata['stats'] = {'min_year': 1950, 'max_year': 2012, 'num_papers': 70, 'avg_papers': 1.1, 'num_refs': 147, 'avg_refs': 2, 'num_cites': 1199, 'avg_cites': 17}
    # rdata['navbarOption'] = {'optionlist': [{'id': 'author', 'name': 'Author'}, {'id': 'conference', 'name': 'Conference'}, {'id': 'journal', 'name': 'Journal'}, {'id': 'institution', 'name': 'Institution'}, {'id': 'paper', 'name': 'Paper'}], 'selectedKeyword': '', 'selectedOption': {'id': 'author', 'name': 'Author'}}
    # rdata['yearSlider'] = {'title': 'Publications range', 'pubrange': [1950, 2012, 63], 'citerange': [1950, 2018, 69], 'pubChart': [], 'citeChart': [], 'selected': {'pub_lower': 1950, 'pub_upper': 2012, 'cit_lower': 1950, 'cit_upper': 2018, 'self_cite': 'false', 'icoauthor': 'true', 'cmp_ref': 'false', 'num_leaves': 25, 'order': 'ratio'}}
    # rdata['curated'] = curated_flag
    # rdata['conf'] = rdata['inst'] = rdata['fos'] = [{'nodes': [], 'links': [], 'bars': [], 'total': 0}] * 3
    # rdata['author'] = [author_flower] * 3
    return render(request, "flower.html", rdata)




@csrf_exempt
def resubmit(request):
    option = request.POST.get('option')
    keyword = request.POST.get('keyword')

    session = json.loads(request.POST.get("session"))

    cache        = session['cache']
    coauthors    = session['coauthors']
    flower_name  = session['flower_name']
    entity_names = session['entity_names']

    flower_config = default_config()
    flower_config['self_cite'] = request.POST.get('selfcite') == 'true'
    flower_config['icoauthor'] = request.POST.get('coauthor') == 'true'
    flower_config['reference'] = request.POST.get('cmp_ref') == 'true'
    flower_config['pub_lower'] = int(request.POST.get('from_pub_year'))
    flower_config['pub_upper'] = int(request.POST.get('to_pub_year'))
    flower_config['cit_lower'] = int(request.POST.get('from_cit_year'))
    flower_config['cit_upper'] = int(request.POST.get('to_cit_year'))
    flower_config['num_leaves'] = int(request.POST.get('numpetals'))
    flower_config['order'] = request.POST.get('petalorder')

    print(flower_config['order'])

    if flower_config['reference']: # Do not limit the size of new flower
        flower_config['num_leaves'] = 5000

    session['year_ranges'] = {'pub_lower': flower_config['pub_lower'], 'pub_upper': flower_config['pub_upper'], 'cit_lower': flower_config['cit_lower'], 'cit_upper': flower_config['cit_upper']}
    print(session['year_ranges'])

    # Recompute flowers
    paper_information = paper_info_db_check_multiquery(cache) # API

    ### PAPER MODIFICATIONS ###
    # Filter for Paper Year different
    max_year_paper = max(paper_information, key=lambda x: x['Year'])['Year']
    new_paper_information = list()
    for paper in paper_information:
        if paper['Year'] > max_year_paper - 100:
            new_paper_information.append(paper)
    paper_information = new_paper_information
    ### PAPER MODIFICATIONS ###

    score_df = score_paper_info_list(paper_information, self=entity_names)

    # Work function
    make_flower = lambda x: gen_flower_data(score_df, x, entity_names,
            flower_name, config=flower_config)

    # Concurrently calculate the aggregations
    # Concurrent map
    if settings.MULTIPROCESS:
        p = multiprocess.Pool(NUM_THREADS)
        flower_res = p.map(make_flower, flower_leaves)
    else: # temporary fix
        flower_res = [make_flower(v) for v in flower_leaves]

    # Reduce
    flower_info = list()
    for _, f_info in flower_res:
        flower_info.append(f_info)

    # filter flower nodes by reference
    if flower_config['reference']:
        reference_flower = session["reference_flower"]

        new_flower_info = [[], [], [], []]

        orig_flower = list(zip(*flower_info))
        for ref_flower, info_flower in zip(reference_flower, orig_flower):
            cmp_flower = compare_flowers(ref_flower, info_flower)
            for i in range(len(flower_info)):
                new_flower_info[i].append(cmp_flower[i])

        for i in range(len(new_flower_info)):
            flower_info[i] = new_flower_info[i]

    data = {
        "author": flower_info[0],
        "conf"  : flower_info[1],
        "inst"  : flower_info[2],
        "fos"   : flower_info[3],
        "navbarOption": get_navbar_option(keyword, option)
    }

    stats = get_stats(paper_information, flower_config['pub_lower'], flower_config['pub_upper'])
    data['stats'] = stats

    # Update the node_info cache
    #session['node_info'] = node_info
    data["session"] = session
    return JsonResponse(data, safe=False)


def conf_journ_to_display_names(papers):
    conf_journ_ids = {"ConferenceSeriesIds": [], "JournalIds": []}
    for paper in papers.values():
        if "ConferenceSeriesId" in paper: conf_journ_ids["ConferenceSeriesIds"].append(paper["ConferenceSeriesId"])
        if "JournalId" in paper: conf_journ_ids["JournalIds"].append(paper["JournalId"])
    conf_journ_display_names = get_conf_journ_display_names(conf_journ_ids)
    for paper in papers.values():
        try:
            if "ConferenceSeriesId" in paper: paper["ConferenceName"] = conf_journ_display_names["Conference"][paper["ConferenceSeriesId"]]
            if "JournalId" in paper: paper["JournalName"] = conf_journ_display_names["Journal"][paper["JournalId"]]
        except:
            print("Unable to match display name for journal/conference")
    return papers

@csrf_exempt
def get_publication_papers(request):
    start = datetime.now()
    # request should contain the ego author ids and the node author ids separately
    print(request.POST)
    request_data = json.loads(request.POST.get("data_string"))
    session = request_data.get("session")

    pub_year_min = int(request.POST.get("pub_year_min"))
    pub_year_max = int(request.POST.get("pub_year_max"))
    paper_ids = session['cache']
    papers = paper_info_db_check_multiquery(paper_ids)
    papers = [paper for paper in papers if (paper["Year"] >= pub_year_min and paper["Year"] <= pub_year_max)]
    papers = conf_journ_to_display_names({paper["PaperId"]: paper for paper in papers})
    print((datetime.now()-start).total_seconds())
    return JsonResponse({"papers": papers, "names": session["entity_names"]+ session["node_info"]}, safe=False)

@csrf_exempt
def get_citation_papers(request):
    start = datetime.now()
    # request should contain the ego author ids and the node author ids separately
    print(request.POST)

    request_data = json.loads(request.POST.get("data_string"))
    session = request_data.get("session")

    cite_year_min = int(request.POST.get("cite_year_min"))
    cite_year_max = int(request.POST.get("cite_year_max"))
    pub_year_min = int(request.POST.get("pub_year_min"))
    pub_year_max = int(request.POST.get("pub_year_max"))
    paper_ids = session['cache']
    papers = paper_info_db_check_multiquery(paper_ids)
    cite_papers = [[citation for citation in paper["Citations"] if (citation["Year"] >= cite_year_min and citation["Year"] <= cite_year_max)] for paper in papers if (paper["Year"] >= pub_year_min and paper["Year"] <= pub_year_max)]
    citations = sum(cite_papers,[])
    citations = conf_journ_to_display_names({paper["PaperId"]: paper for paper in citations})

    print((datetime.now()-start).total_seconds())
    return JsonResponse({"papers": citations, "names": session["entity_names"] + session["node_info"],"node_info": session["node_information_store"]}, safe=False)


def get_entities(paper):
    ''' Gets the entities of a paper
    '''
    authors      = [author["AuthorName"] for author in paper["Authors"]]
    affiliations = [author["AffiliationName"] for author in paper["Authors"] if "AffiliationName" in author]
    conferences = [paper["ConferenceName"]] if ("ConferenceName" in paper) else []
    journals = [paper["JournalName"]] if ("JournalName" in paper) else []
    fieldsofstudy = [fos["FieldOfStudyName"] for fos in paper["FieldsOfStudy"] if fos["FieldOfStudyLevel"] == 1] if ("FieldsOfStudy" in paper) else []

    return authors, affiliations, conferences, journals, fieldsofstudy


NODE_INFO_FIELDS = ["PaperTitle", "Authors", "PaperId", "Year", "ConferenceName",
        "ConferenceSeriesId", "JournalName", "JournalId"]


def get_node_info_single(request, entity, entity_type, year_ranges):
    # Determine the citation range
    pub_lower = year_ranges["pub_lower"]
    pub_upper = year_ranges["pub_upper"]
    cit_lower = year_ranges["cit_lower"]
    cit_upper = year_ranges["cit_upper"]

    # Get paper to get information from
    request_data = json.loads(request.POST.get("data_string"))
    session = request_data.get("session")
    papers = paper_info_db_check_multiquery(session["cache"])

    # Get coauthors list to filter
    if session['icoauthor'] == 'false':
        coauthors = session['coauthors']
    else:
        coauthors = list()

    # Get self_citation list to filter
    if session['self_cite'] == 'false':
        self = session['entity_names']
    else:
        self = list()

    # Results
    papers_to_send = dict()
    links = dict()

    for paper in papers:
        # Publication range filter
        if paper["Year"] < pub_lower or paper["Year"] > pub_upper:
            continue

        for link_type in ["References", "Citations"]:
            for rel_paper in paper[link_type]:
                # Citation range filter
                if link_type == "Citations" and \
                        (rel_paper["Year"] < cit_lower or rel_paper["Year"] > cit_upper):
                                continue

                # Get fields
                auth, inst, conf, jour, fos = get_entities(rel_paper)
                fields = dict()
                fields['author'] = set(auth)
                fields['inst'] = set(inst)
                fields['conf'] = set(conf + jour)
                fields['fos']  = set(fos)

                check = dict()
                check['author'] = coauthors + self
                check['inst'] = coauthors + self
                check['conf'] = coauthors
                check['fos']  = list()

                skip = False
                for n_type, check_val in check.items():
                    if not set(check_val).isdisjoint(fields[entity_type]):
                        skip = True
                        break
                if skip:
                    continue

                if entity not in fields[entity_type]:
                    continue

                papers_to_send[paper["PaperId"]] = {k:v for k,v in paper.items() if k in NODE_INFO_FIELDS}
                papers_to_send[paper["PaperId"]] = add_author_order(papers_to_send[paper["PaperId"]])

                papers_to_send[rel_paper["PaperId"]] = {k:v for k,v in rel_paper.items() if k in NODE_INFO_FIELDS}
                papers_to_send[rel_paper["PaperId"]] = add_author_order(papers_to_send[rel_paper["PaperId"]])

                if link_type == "Citations":
                    if paper["PaperId"] in links:
                        links[paper["PaperId"]]["reference"].append(rel_paper["PaperId"])
                    else:
                        links[paper["PaperId"]] = {"reference": [rel_paper["PaperId"]], "citation": list()}
                else:
                    if paper["PaperId"] in links:
                        links[paper["PaperId"]]["citation"].append(rel_paper["PaperId"])
                    else:
                        links[paper["PaperId"]] = {"citation": [rel_paper["PaperId"]], "reference": list()}

    paper_sort_func = lambda x: -papers_to_send[x]["Year"]
    links = sorted([{"citation": sorted(link["citation"],key=paper_sort_func), "reference": sorted(link["reference"],key=paper_sort_func), "ego_paper": key} for key, link in links.items()], key=lambda x: paper_sort_func(x["ego_paper"]))

    return {"node_name": entity, "node_type": entity_type, "node_links": links, "paper_info": papers_to_send}


@csrf_exempt
def get_node_info(request):
    request_data = json.loads(request.POST.get("data_string"))
    node_name = request_data.get("name")
    node_type = request_data.get("node_type")
    print(node_name, node_type)
    session = request_data.get("session")
    entities = session["entity_names"]
    year_ranges = session["year_ranges"]
    flower_name = session["flower_name"]

    data = get_node_info_single(request, node_name, node_type, year_ranges)
    data["node_name"] = node_name
    data["flower_name"] = flower_name
    data["max_page"] = math.ceil(len(data["node_links"]) / 5)
    data["node_links"] = data["node_links"][0:min(5, len(data["node_links"]))]
    return JsonResponse(data, safe=False)

@csrf_exempt
def get_next_node_info_page(request):
    request_data = json.loads(request.POST.get("data_string"))
    node_name = request_data.get("name")
    node_type = request_data.get("node_type")
    session = request_data.get("session")
    entities = session["entity_names"]
    year_ranges = session["year_ranges"]
    flower_name = session["flower_name"]
    page = int(request_data.get("page"))

    node_info = get_node_info_single(request, node_name, node_type, year_ranges)
    page_length = 5
    page_info = {"paper_info": node_info["paper_info"], "node_links": node_info["node_links"][0+page_length*(page-1):min(page_length*page, len(node_info["node_links"]))]}
    print(page)
    return JsonResponse(page_info, safe=False)
