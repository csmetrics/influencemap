import os, json, requests, sys
import http.client, urllib.request, urllib.parse, urllib.error, base64
from parse_academic_search import *

MAS_URL_PREFIX = "https://api.labs.cognitive.microsoft.com"
headers = {
    # Request headers
    #'Ocp-Apim-Subscription-Key': 'a27d17cc1a6044f5bb6accf68e10eefa',   # original
    'Ocp-Apim-Subscription-Key': '4698d5e7b0244e828d1dc21134238650',    # bens
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

entity_search_details = {
  "author": {
    "expr": "AuN='{}'",
    "attributes": "AuN,DAuN,Id,CC,ECC,E",
    "link_to_paper": "AA.AuId"
  },
  "institution": {
    "expr": "AfN='{}'",
    "attributes": "Id,AfN,DAfN,CC,ECC,E",
    "link_to_paper": "AA.AfId" 
  },
  "conference": {
    "expr": "CN='{}'",
    "attributes": "Id,CN,DCN,CC,ECC,F.FN,F.FId,PC",
    "link_to_paper": "C.CId" 
  },
  "journal": {
    "expr": "JN='{}'",
    "attributes": "Id,DJN,JN,CC,ECC,PC",
    "link_to_paper": "J.JId" 
  },
    "paper": {
    "expr": "Ti='{}'",
    "attributes": "Id,Ti,Y,CC,AA.AuN,AA.AuId,RId"
  },

}

def get_search_results(keyword, entityType):
    search_details = entity_search_details[entityType]
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate?mode=json")
    query = {
      "expr": search_details['expr'].format(keyword),
      "count": 100,
      "attributes": search_details['attributes']
    }
    data = query_academic_search("get", url, query)

    return data
    

def get_papers_from_entity_ids(entity_ids, entityType):
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    base_string = "Composite("+entity_search_details[entityType]['link_to_paper']+"={})"
    or_string = or_query_builder(base_string, entity_ids)
    expr = "{}".format(or_string)
    query = {
      "expr": expr,
      "count": 10000,
      "offset": 0,
      "attributes": "Ti,AA.AuId,AA.AuN,AA.AfN,AA.AfId,L,Y,D,CC,ECC,F.FN,C.CN,C.CId,J.JId,J.JN"
      # "attributes": "prob,Id,Ti,Y,CC,AA.AuN,AA.AuId,RId"
    }

    data = query_academic_search("get", url, query)
    return data

def get_entities_from_search(keyword, entityType):
  data = get_search_results(keyword, entityType)
  data = parse_search_results(data, entityType)
  if entityType in ['author', 'conference', 'institution', 'journal']:
      eids = [entity['eid'] for entity in data]
      papers = get_papers_from_entity_ids(eids, entityType)
      # print(papers['entities'][0])
      papers = parse_search_results(papers, 'paper')
      data = link_papers_to_entities(papers, data, entityType)
      data = [x for x in data.values()]

  for entity in data:
      entity['entity-type'] = entityType
  return data

def printDict(d):
    print("dict():")
    for k,v in d.items():
        if k == 'papers':
            v = v[:1]
        print("\t{}\t{}".format(k,v))
