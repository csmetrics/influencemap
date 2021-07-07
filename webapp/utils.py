import json
import os
import pathlib

from core.search.elastic import *
from core.flower.high_level_get_flower import default_config
from webapp.shortener import url_encode_info

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

GALLERY_DATA_PATH = pathlib.Path("webapp/data")


def read_gallery_group(filename):
    try:
        f = open(filename)
    except FileNotFoundError:
        return []
    with f:
        group_list = json.load(f)
    for entry in group_list:
        entity_ids = entry['EntityIds']
        entry['FlowerUrl'] = url_encode_info(
            author_ids=entity_ids.get('AuthorIds', ()),
            affiliation_ids=entity_ids.get('AffiliationIds', ()),
            conference_series_ids=entity_ids.get('ConferenceIds', ()),
            field_of_study_ids=entity_ids.get('FieldOfStudyIds', ()),
            journal_ids=entity_ids.get('JournalIds', ()),
            paper_ids=entity_ids.get('PaperIds', ()),
            name=entry['DisplayName'],
            curated=True)
    return sorted(
        group_list, key=lambda x: (x.get("Year", 0), x["DisplayName"]))


def load_gallery():
    with open(GALLERY_DATA_PATH / "browse_list.json") as fh:
        browse_list = json.load(fh)
    for group in browse_list:
        for subgroup in group["subgroups"]:
            if subgroup["type"] == "inner":
                group_file = GALLERY_DATA_PATH / (subgroup["tag"] + ".json")
                subgroup["docs"] = read_gallery_group(group_file)
            else: # subgroup["type"] == "outer":
                for subsubgroup in subgroup["subgroups"]:
                    if subsubgroup["type"] == "inner":
                        group_file_name = subsubgroup["tag"] + ".json"
                        group_file = GALLERY_DATA_PATH / group_file_name
                        subsubgroup["docs"] = read_gallery_group(group_file)
    return browse_list

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

def get_url_config(query):
    if "pmin" in query:
        return {
            "pub_lower": int(query.get("pmin")),
            "pub_upper": int(query.get("pmax")),
            "cit_lower": int(query.get("cmin")),
            "cit_upper": int(query.get("cmax")),
            "self_cite": query.get("selfcite") == "true",
            "icoauthor": query.get("coauthor") == "true",
            "num_leaves": int(query.get("node")),
            "order": query.get("order"),
            "cmp_ref": query.get("cmp_ref") == "true",
        }
    return None

def add_author_order(paper_info):
    '''
    '''
    author_order = author_order_query(paper_info['PaperId'])

    for author in paper_info['Authors']:
        if author['AuthorId'] not in author_order:
            continue
        author['AuthorOrder'] = author_order[author['AuthorId']]

    return paper_info
