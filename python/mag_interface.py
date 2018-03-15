import os, json, requests
import http.client, urllib.request, urllib.parse, urllib.error, base64
import pandas as pd
import entity_type as ent
import functools
from datetime import datetime
from config import *

header = {
    # Request headers
    'Ocp-Apim-Subscription-Key': API_KEYS[0]
}


def query_academic_search(type, url, query):
    """
        Helper for requesting data from API.
    """
    if type == "get":
        response = requests.get(url, params=urllib.parse.urlencode(query), headers=header)
    elif type == "post":
        response = requests.post(url, json=query, headers=header)
        print("ERROR: problem with the request.")
        print(response.content)
    return json.loads((response.content).decode("utf-8"))


def to_datetime(strtime):
    """
        Turns string format of MAG dates into datetime object.
    """
    return datetime.datetime.strptime(strtime, '%Y-%m-%dT%X')


def api_get_list(field_list):
    """
        Turns a list of string fields to a list of get operators.
    """
    get_list = ['get("{}")'.format(f) for f in field_list]
    return 'new List<string>{{ {} }}'.format(','.join(get_list))


def some_func(paper_ids, e_type):
    """
        Citation information
        paper_dict: [ { CellID: int, PaperIDs: [int]} ]
    """
    init_query = {
            "type": "Paper",
            "id": paper_ids
        }
    move = ['CitationIDs']
    fields = ['AuthorIDs', 'ConferenceSeriesID', 'JournalID', 'AffiliationIDs',\
              'FieldOfStudyIDs']
    name_return = ["Name", "ShortName"]
    get_name = 'v => Action.Return, {}'


def auth_name_to_auth_id(auth_name):
    """
        Turns an author name into its set of ids.
    """
    query = {
        "path": "/author",
        "author": {
            "type": "Author",
            "match": {
                "Name": auth_name
                }
            }
        }

    data = query_academic_search('post', JSON_URL, query)
    return list(map(lambda x : x[0]['CellID'], data['Results']))

def auth_id_to_citation_mask(auth_ids):
    """
        Turns an author ids into a list of papers associated to the ids.
    """
    query = {
        "path": "/authors/PaperIDs/paper/CitationIDs/cites",
        "authors": {
            "type": "Author",
            "id": auth_ids
            },
        "paper": {
            "select": [
                "PublishDate",
                "AuthorIDs"
                ]
            },
        "cites": {
            "select": [
                "PublishDate",
                "AuthorIDs"
                ]
            }
        }

    data = query_academic_search('post', JSON_URL, query)
    data_sc = list()
    for auth, ego, cite in data['Results']:
        row = dict()
        row['paper_ego'] = ego['CellID']
        row['paper_other'] = cite['CellID']
        row['auth_id'] = auth['CellID']
        row['weight'] = len(ego['AuthorIDs'])
        row['self_cite'] = auth['CellID'] in cite['AuthorIDs']
        row['date_ego'] = ego['PublishDate']
        row['date_other'] = cite['PublishDate']
        data_sc.append(row)

    return pd.DataFrame(data_sc)

def auth_id_to_reference_mask(auth_ids):
    """
        Turns an author ids into a list of papers associated to the ids.
    """
    query = {
        "path": "/authors/PaperIDs/paper/ReferenceIDs/refs",
        "authors": {
            "type": "Author",
            "id": auth_ids
            },
        "paper": {
            "select": [
                "PublishDate",
                ]
            },
        "cites": {
            "select": [
                "PublishDate",
                "AuthorIDs"
                ]
            }
        }

    data = query_academic_search('post', JSON_URL, query)
    data_sc = list()
    for auth, ego, ref in data['Results']:
        row = dict()
        row['paper_ego'] = ego['CellID']
        row['paper_other'] = ref['CellID']
        row['auth_id'] = auth['CellID']
        row['weight'] = len(ref['AuthorIDs'])
        row['self_cite'] = auth['CellID'] in ref['AuthorIDs']
        row['date_ego'] = ego['PublishDate']
        row['date_other'] = ref['PublishDate']
        data_sc.append(row)

    return pd.DataFrame(data_sc)





def paper_id_to_citation_score(paper_map, entity):
    """
        Turns an author ids into a list of papers associated to the ids.
    """
    entity_ids = set([p['CellID'] for p in paper_map])
    paper_ids = list(itertools.chain.from_iterable( \
                    [p['PaperIDs'] for p in paper_map]))

    query = {
        "path": "/paper/CitationIDs/cites",
        "paper": {
            "type": "Paper",
            "id": paper_ids,
            "select": [
                "PublishDate",
                entity.api_key
                ]
            },
        "cites": {
            "select": [
                "PublishDate",
                entity.api_key
                ]
            }
        }

    data = query_academic_search('post', JSON_URL, query)
    data_sc = list()
    for ego, cite in data['Results']:
        row = dict()
        row['info_from'] = ego['CellID']
        #row['paper_other'] = cite['CellID']
        row['paper_id'] = cite['CellID']
        row['influenced'] = 1 #/ len(ego['AuthorIDs'])
        row['influencing'] = 0
        row['self_cite'] = 0 if entity_ids.disjoint(cite['AuthorIDs']) else 1
        #row['date_ego'] = ego['PublishDate']
        row['influence_year'] = cite['PublishDate']
        data_sc.append(row)

    return pd.DataFrame(data_sc)


def paper_id_to_reference_score(paper_map, entity):
    """
        Turns an author ids into a list of papers associated to the ids.
    """
    entity_ids = set([p['CellID'] for p in paper_map])
    paper_ids = list(itertools.chain.from_iterable( \
                    [p['PaperIDs'] for p in paper_map]))

    query = {
        "path": "/paper/ReferenceIDs/refs",
        "paper": {
            "type": "Paper",
            "id": paper_ids,
            "select": [
                "PublishDate",
                entity.api_key
                ]
            },
        "refs": {
            "select": [
                "PublishDate",
                entity.api_key
                ]
            }
        }

    data = query_academic_search('post', JSON_URL, query)
    data_sc = list()
    for ego, refs in data['Results']:
        row = dict()
        row['info_from'] = ego['CellID']
        #row['paper_other'] = refs['CellID']
        row['paper_id'] = refs['CellID']
        row['influenced'] = 0
        row['influencing'] = 1 #/ len(refs['AuthorIDs'])
        row['self_cite'] = 0 if entity_ids.disjoint(refs['AuthorIDs']) else 1
        row['influence_year'] = ego['PublishDate']
        #row['influence_year'] = cite['PublishDate']
        data_sc.append(row)

    return pd.DataFrame(data_sc)


def gen_score_df(citation_df, reference_df):
    """
    """
    return pd.concat([citation_df, reference_df])


def score_entity(score_df, entity_map):
    """
    """
    ego, leaves = entity_map.get_map()
    paper_ids = list(set(score_df['paper_id']))
    data_dict = list()

    for e_type in leaves:
        entity_query = {
            "path": "/paper/{}/entity".format(e_type.api_key),
            "paper": {
                 "type": "Paper",
                 "id": paper_ids
                 },
            "entity": {
                 "select": [ e_type.api_name ]
                 }

        data = query_academic_search('post', JSON_URL, query)
        for line in data['Results']:
            row = dict()
            row['paper_id'] = line['CellID']
            row['entity_id'] = line[e_type.api_name]
            data_dict.append(row)

     entity_df = pd.DataFrame(data_dict)
     return pd.merge(entity_df, score_df, on='paper_id', sort=False)
