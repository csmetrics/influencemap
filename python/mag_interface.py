import os, json, requests
import http.client, urllib.request, urllib.parse, urllib.error, base64
import pandas as pd
import functools
from datetime import datetime
from config import *

header = {
    # Request headers
    'Ocp-Apim-Subscription-Key': API_KEYS[0]
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
    return json.loads((response.content).decode("utf-8"))

def to_datetime(strtime):
    return datetime.strptime(strtime, '%Y-%m-%dT%X')

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

    return(pd.DataFrame(data_sc))

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

    return(pd.DataFrame(data_sc))
