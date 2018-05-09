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

API_IDX = 1

header = {
    # Request headers
    'Ocp-Apim-Subscription-Key': API_KEYS[API_IDX]
}


print('Using key {} with key: {}'.format(API_IDX, API_KEYS[API_IDX]))


def query_academic_search(type, url, query):
    if type == "get":
        response = requests.get(url, params=urllib.parse.urlencode(query), headers=header)
    elif type == "post":
        response = requests.post(url, json=query, headers=header)
        print(response.status_code)
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
