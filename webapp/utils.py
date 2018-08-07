import os
from core.search.academic_search import *
from webapp.elastic import query_browse_group, query_cache_paper_info, query_author_group, query_paper_group, get_names_from_conference_ids, get_names_from_journal_ids, get_names_from_affiliation_ids
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
        config = [
            int(query.get("pmin")), int(query.get("pmax")),
            int(query.get("cmin")), int(query.get("cmax")),
            query.get("selfcite") == "true",
            query.get("coauthor") == "true"
        ]
    document_id = query.get("id")
    document = query_browse_group(document_id)
    return document, "author", config


def get_all_paper_ids(entityIds):
    paper_ids = [] + entityIds['PaperIds'] if "PaperIds" in entityIds else []
    if "AuthorIds" in entityIds and entityIds["AuthorIds"] != []: paper_ids += get_papers_from_author_ids(entityIds['AuthorIds'])
    if "ConferenceIds" in entityIds and entityIds["ConferenceIds"] != []: paper_ids += get_papers_from_conference_ids(entityIds['ConferenceIds'])
    if "AffiliationIds" in entityIds and entityIds["AffiliationIds"] != []: paper_ids += get_papers_from_affiliation_ids(entityIds['AffiliationIds'])
    if "JournalIds" in entityIds and entityIds["JournalIds"] != []: paper_ids += get_papers_from_journal_ids(entityIds['JournalIds'])
    return paper_ids


def get_all_normalised_names(entityIds):
    normalised_names = []
    if "AuthorIds" in entityIds and entityIds["AuthorIds"] != []: normalised_names += get_names_from_author_ids(entityIds['AuthorIds'])
    if "ConferenceIds" in entityIds and entityIds["ConferenceIds"] != []: normalised_names += get_names_from_conference_ids(entityIds['ConferenceIds'])
    if "AffiliationIds" in entityIds and entityIds["AffiliationIds"] != []: normalised_names += get_names_from_affiliation_ids(entityIds['AffiliationIds'])
    if "JournalIds" in entityIds and entityIds["JournalIds"] != []: normalised_names += get_names_from_journal_ids(entityIds['JournalIds'])

    return normalised_names
