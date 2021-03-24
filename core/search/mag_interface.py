import json
from datetime import datetime

import http.client
import requests
import urllib.error
import urllib.parse
import urllib.request

from core.config import *


class APIKeyError(Exception):
    pass


def get_header(idx, keys):
    # Request headers
    header = {
        'Ocp-Apim-Subscription-Key': keys[idx]
        }
    return header


def query_academic_search(type, url, query):
    i = 0
    processing = True
    keys = API_KEYS
    header = get_header(i, keys)

    # Keep trying API keys until failure or results
    while processing:
        if type == "get":
            response = requests.get(url, params=urllib.parse.urlencode(query), headers=header)
        elif type == "post":
            response = requests.post(url, data=query, headers=header)
            #print(response.status_code)
        if response.status_code == 401:
            print(keys[i])
        if response.status_code != 200:
            print("return statue: " + str(response.status_code))
            print(header)
            print("ERROR: problem with the request.")
            print(response.content)
        if response.status_code not in [429, 403]:
            # 429 Rate limit, 403 Quota Exceeded
            processing = False
        if i >= MAX_API - 1:
            raise APIKeyError("Out of API keys")
        else:
            i += 1
            header = get_header(i, keys)

    return json.loads((response.content).decode("utf-8"))
