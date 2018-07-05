import os, json, requests
import http.client, urllib.request, urllib.parse, urllib.error, base64
import pandas as pd
import functools
import itertools
import operator
import random
import sys
from datetime import datetime
from core.config import *

get_header = lambda x, keys : {
    # Request headers
    'Ocp-Apim-Subscription-Key': keys[x]
}


#print('Using key {} with key: {}'.format(API_IDX, API_KEYS[API_IDX]))


def query_academic_search(type, url, query):
    i = 0
    processing = True
    keys = API_KEYS
    #random.shuffle(keys)
    header = get_header(i, keys)

    # Keep trying API keys until failure or results
    while processing:
        if type == "get":
            response = requests.get(url, params=urllib.parse.urlencode(query), headers=header)
        elif type == "post":
            response = requests.post(url, json=query, headers=header)
            #print(response.status_code)
        if response.status_code == 401:
            print(keys[i])
        if response.status_code != 200:
            print("return statue: " + str(response.status_code))
            print(header)
            print("ERROR: problem with the request.")
            print(response.content)
            #exit()
        if response.status_code not in [429, 403] or i >= MAX_API - 1: # 429 Rate limit, 403 Quota Exceeded
            processing = False
        else:
            i += 1
            header = get_header(i, keys)

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
