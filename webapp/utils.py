import os
from core.search.academic_search import *
from webapp.elastic import *
from core.search.query_paper import conference_paper_query
from core.search.query_paper import journal_paper_query
from core.search.query_name import conference_name_query
from core.search.query_name import journal_name_query
from core.search.query_name import author_name_query
from core.search.query_name import affiliation_name_query

from core.flower.high_level_get_flower import default_config

import matplotlib.pylab as plt
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# option list for radios
optionlist = [  # option list
    {"id":"author", "name":"Author"},
    {"id":"conference", "name":"Conference"},
    {"id":"journal", "name":"Journal"},
    {"id":"institution", "name":"Institution"},
    {"id":"paper", "name": "Paper"}]

# initialise as no autocomplete lists yet (wait until needed)
autoCompleteLists = {}


def printNested(obj, indent=0):
    if type(obj) in [list,tuple,set]:
        for elem in obj:
            printNested(elem, indent)
    elif type(obj) is dict:
        for key, value in obj.items():
            print((indent*"\t")+str(key)+":")
            printNested(value,indent+1)
    else:
        print(indent*"\t"+str(obj))


def printDict(d, nested=False):
    if not nested:
        for k,v in d.items():
            print('k: {}\tv: {}'.format(k,v))
    else:
        printNested(d, 0)


def loadList(entity):
    path = os.path.join(BASE_DIR, "webapp/cache/"+entity+"List.txt")
    if entity == 'paper':
        return []
    elif entity not in autoCompleteLists.keys():
        with open(path, "r") as f:
            autoCompleteLists[entity] = [name.strip() for name in f]
        autoCompleteLists[entity] = list(set(autoCompleteLists[entity]))
    return autoCompleteLists[entity]

def get_navbar_option(keyword = "", option = ""):
    return {
        "optionlist": optionlist,
        "selectedKeyword": keyword,
        "selectedOption": [opt for opt in optionlist if opt['id'] == option][0] if option != "" else optionlist[0],
    }

def get_url_query(query):
    config = None
    if "pmin" in query:
        config = {
            "pub_lower": int(query.get("pmin")),
            "pub_upper": int(query.get("pmax")),
            "cit_lower": int(query.get("cmin")),
            "cit_upper": int(query.get("cmax")),
            "self_cite": query.get("selfcite") == "true",
            "icoauthor": query.get("coauthor") == "true",
            "num_leaves": int(query.get("node")),
            "order": query.get("order"),
            "reference": query.get("ref") == "true",
        }

    document_id = query.get("id")
    document = query_browse_group(document_id)
    return document, "author", config


def get_all_paper_ids(entityIds):
    paper_ids = entityIds['PaperIds'] if "PaperIds" in entityIds else []
    if "AuthorIds" in entityIds and entityIds["AuthorIds"] != []: paper_ids += get_papers_from_author_ids(entityIds['AuthorIds'])
    #if "ConferenceIds" in entityIds and entityIds["ConferenceIds"] != []: paper_ids += get_papers_from_conference_ids(entityIds['ConferenceIds'])
    if "ConferenceIds" in entityIds and entityIds["ConferenceIds"] != []: paper_ids += conference_paper_query(entityIds['ConferenceIds'])
    if "AffiliationIds" in entityIds and entityIds["AffiliationIds"] != []: paper_ids += get_papers_from_affiliation_ids(entityIds['AffiliationIds'])
    #if "JournalIds" in entityIds and entityIds["JournalIds"] != []: paper_ids += get_papers_from_journal_ids(entityIds['JournalIds'])
    if "JournalIds" in entityIds and entityIds["JournalIds"] != []: paper_ids += journal_paper_query(entityIds['JournalIds'])
    return paper_ids


def get_all_normalised_names(entityIds):
    normalised_names = []
    if "AuthorIds" in entityIds and entityIds["AuthorIds"] != []: normalised_names += author_name_query(entityIds['AuthorIds'])
    if "ConferenceIds" in entityIds and entityIds["ConferenceIds"] != []: normalised_names += conference_name_query(entityIds['ConferenceIds'])
    if "AffiliationIds" in entityIds and entityIds["AffiliationIds"] != []: normalised_names += affiliation_name_query(entityIds['AffiliationIds'])
    if "JournalIds" in entityIds and entityIds["JournalIds"] != []: normalised_names += journal_name_query(entityIds['JournalIds'])

    return normalised_names

def get_conf_journ_display_names(entityIds):
    display_names = dict()
    if "ConferenceSeriesIds" in entityIds and entityIds["ConferenceSeriesIds"] != []: display_names["Conference"] = get_display_names_from_conference_ids(entityIds['ConferenceSeriesIds'])
    if "JournalIds" in entityIds and entityIds["JournalIds"] != []: display_names["Journal"] = get_display_names_from_journal_ids(entityIds['JournalIds'])

    return display_names

def add_author_order(paper_info):
    '''
    '''
    author_order = author_order_query(paper_info['PaperId'])

    for author in paper_info['Authors']:
        author['AuthorOrder'] = author_order[author['AuthorId']]

    return paper_info
