import os, json, requests
import http.client, urllib.request, urllib.parse, urllib.error, base64

MAS_URL_PREFIX = "http://westus.api.cognitive.microsoft.com"
headers = {
    # Request headers
    'Ocp-Apim-Subscription-Key': 'a27d17cc1a6044f5bb6accf68e10eefa',
}

def query_academic_search(type, url, query):
    if type == "get":
        response = requests.get(url, params=urllib.parse.urlencode(query), headers=headers)
    elif type == "post":
        response = requests.post(url, json=query, headers=headers)
    if response.status_code != 200:
        print("return statue: " + str(response.status_code))
        print("ERROR: problem with the request.")
        print(response.content)
        #exit()
    return json.loads((response.content).decode("utf-8"))

def get_papers_from_field_of_study(field, citation):
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    query = {
      "expr": "And(Composite(F.FN=='{}'), CC>={}, CC<{})".format(field, citation[0], citation[1]),
      "count": 1000,
      "offset": 0,
    #   "attributes": "prob,Id,Ti,Y,CC,AA.AuN,AA.AuId,RId"
      "attributes": "prob,Id,Ti,Y,CC,AA.AuN,AA.AuId"
    }
    data = query_academic_search("get", url, query)
    return data

def get_paperinfo_from_title(paper_title):
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/interpret")
    data = query_academic_search("get", url, {"query": paper_title})
    # print(data)
    interpret_expr = data["interpretations"][0]["rules"][0]["output"]["value"]
    # print(interpret_expr)
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    query = {
      "expr": interpret_expr,
      "attributes": "Id"
    }
    data = query_academic_search("get", url, query)
    return data


def get_papers_from_author(author):
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    query = {
      "expr": "Composite(AA.AuN=='{}')".format(author),
      "count": 1000,
      "offset": 0,
      "attributes": "prob,Id,Ti,Y,CC,AA.AuN,AA.AuId,RId"
    }
    data = query_academic_search("get", url, query)
    return data

def get_citations_from_papers(paper_ids):
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/graph/search?mode=json")
    query = {
      "path": "/paper",
      "paper": {
        "type": "Paper",
        "id": paper_ids,
        "select": [ "OriginalTitle", "CitationCount", "CitationIDs", "ReferenceIDs" ]
      }
    }
    data = query_academic_search("post", url, query)
    return data

def get_authors_from_papers(paper_ids):
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/graph/search?mode=json")
    query = {
      "path": "/paper",
      "paper": {
        "type": "Paper",
        "id": paper_ids,
        "select": [ "AuthorIDs" ]
      }
    }
    data = query_academic_search("post", url, query)
    return data

def get_author_information(author_ids):
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/graph/search?mode=json")
    query = {
      "path": "/author",
      "author": {
        "type": "Author",
        "id": author_ids,
        "select": [ "Name" ]
      }
    }
    data = query_academic_search("post", url, query)
    return data
