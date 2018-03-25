import os, json, requests
import http.client, urllib.request, urllib.parse, urllib.error, base64
import pandas as pd
import entity_type as ent
import functools
import itertools
import operator
import sys
from datetime import datetime
from config import *

header = {
    # Request headers
    'Ocp-Apim-Subscription-Key': API_KEYS[1]
}


def query_academic_search(type, url, query):
    if type == "get":
        response = requests.get(url, params=urllib.parse.urlencode(query), headers=header)
    elif type == "post":
        response = requests.post(url, json=query, headers=header)
    if response.status_code != 200:
        print("return statue: " + str(response.status_code))
        print("ERROR: problem with the request.")
        print(response.content)
        #exit()
    return json.loads((response.content).decode("utf-8"))


def to_datetime(strtime):
    """
        Turns string format of MAG dates into datetime object.
    """
    return datetime.strptime(strtime, '%Y-%m-%dT%X')


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


def auth_name_to_paper_map(auth_name):
    """
    """
    query = {
        "path": "/author",
        "author": {
            "type": "Author",
            "match": {
                "Name": auth_name
                },
            "select": [ "DisplayAuthorName", "PaperIDs" ]
            }
        }

    data = query_academic_search('post', JSON_URL, query)
    res_dict = dict()
    name_dict = dict()
    for entity in data['Results']:
        res_dict[entity[0]['CellID']] = entity[0]['PaperIDs']
        try:
            name_dict[entity[0]['DisplayAuthorName']] += 1
        except KeyError:
            name_dict[entity[0]['DisplayAuthorName']] = 1
    
    return sorted(name_dict.items(), key=operator.itemgetter(1),
                  reverse=True)[0][0], res_dict


def paper_id_to_citation_score(paper_map, entity):
    """
        Turns an author ids into a list of papers associated to the ids.
    """
    entity_ids = set(paper_map.keys())
    paper_ids = list(itertools.chain.from_iterable(paper_map.values()))

    query = {
        "path": "/paper/CitationIDs/cites",
        "paper": {
            "type": "Paper",
            "id": paper_ids,
            "select": [
                "PublishDate",
                entity.api_id
                ]
            },
        "cites": {
            "select": [
                "PublishDate",
                entity.api_id
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
        row['self_cite'] = 0 if entity_ids.isdisjoint(cite['AuthorIDs']) else 1
        #row['date_ego'] = ego['PublishDate']
        row['influence_date'] = to_datetime(cite['PublishDate'])
        data_sc.append(row)

    return pd.DataFrame(data_sc)


def paper_id_to_reference_score(paper_map, entity):
    """
        Turns an author ids into a list of papers associated to the ids.
    """
    entity_ids = set(paper_map.keys())
    paper_ids = list(itertools.chain.from_iterable(paper_map.values()))

    query = {
        "path": "/paper/ReferenceIDs/refs",
        "paper": {
            "type": "Paper",
            "id": paper_ids,
            "select": [
                "PublishDate",
                entity.api_id
                ]
            },
        "refs": {
            "select": [
                "PublishDate",
                entity.api_id
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
        row['self_cite'] = 0 if entity_ids.isdisjoint(refs['AuthorIDs']) else 1
        row['influence_date'] = to_datetime(ego['PublishDate'])
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
            "path": "/paper/{}/entity".format(e_type.api_id),
            "paper": {
                 "type": "Paper",
                 "id": paper_ids,
                 "select": [ e_type.api_id ]
                 },
            "entity": {
                 "select": [ e_type.api_name ]
                 }
            }

        data = query_academic_search('post', JSON_URL, entity_query)
        for paper, entity in data['Results']:
            row = dict()
            row['paper_id'] = paper['CellID']
            row['entity_id'] = entity[e_type.api_name]
            data_dict.append(row)

    entity_df = pd.DataFrame(data_dict)
    weight_influenced = entity_df['paper_id'].value_counts().to_frame('weight').reset_index()

    # Weight scores
    ego_paper_ids = list(set(score_df['info_from']))

    ego_query = {
            "path": "/paper/{}/entity".format(ego.api_id),
            "paper": {
                "type": "Paper",
                "id": ego_paper_ids,
                "select": [ ego.api_id ]
                },
            "entity": {
                "select": [ ego.api_name ]
                }
            }

    info_from_data = query_academic_search('post', JSON_URL, ego_query)
    ego_dict = list()
    for paper, entity in info_from_data['Results']:
        row = dict()
        row['paper_id'] = paper['CellID']
        row['entity_id'] = entity[ego.api_name]
        ego_dict.append(row)

    ego_df = pd.DataFrame(ego_dict)
    weight_influencing = ego_df['paper_id'].value_counts().to_frame('weight').reset_index()

    rename_dict_influenced = {'index': 'paper_id'}
    rename_dict_influencing = {'index': 'info_from'}
    weight_influenced.rename(columns=rename_dict_influenced, inplace=True)
    weight_influencing.rename(columns=rename_dict_influencing, inplace=True)

    score_df = pd.merge(score_df, weight_influenced, how='outer',
                        on='paper_id', sort=False)
    score_df['influenced'] = score_df['influenced'] / score_df['weight']
    score_df.drop('weight', axis=1, inplace=True)

    score_df = pd.merge(score_df, weight_influencing, how='outer',
                        on='info_from', sort=False)
    score_df['influencing'] = score_df['influencing'] / score_df['weight']
    score_df.drop('weight', axis=1, inplace=True)

    entity_score_df = pd.merge(entity_df, score_df, on='paper_id', sort=False)

    return entity_score_df

if __name__ == "__main__":
    name = sys.argv[1]
    paper_map = auth_name_to_paper_map(name)
    citation_score = paper_id_to_citation_score(paper_map, ent.Entity_type.AUTH)
    reference_score = paper_id_to_reference_score(paper_map, ent.Entity_type.AUTH)
    score_df = gen_score_df(citation_score, reference_score)
    score = score_entity(score_df, ent.Entity_map(ent.Entity_type.AUTH, [ent.Entity_type.AUTH]))
    print(score)
