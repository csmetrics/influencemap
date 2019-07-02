import os, json, requests, sys
import http.client, urllib.request, urllib.parse, urllib.error, base64
from core.search.parse_academic_search import *

MAS_URL_PREFIX = "https://api.labs.cognitive.microsoft.com"

import core.search.mag_interface as mag_interface

def query_academic_search(type, url, query):
    return mag_interface.query_academic_search(type, url, query)

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

def get_paperinfo_from_ids(paper_ids):
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    base_string = "Id={}"
    or_string = or_query_builder(base_string, paper_ids)
    expr = "{}".format(or_string)
    query = {
      "expr": expr,
      "count": 10000,
      "offset": 0,
      "attributes": "Ti,Y,AA.AuId,AA.AuN,AA.AfId,AA.AfN"
#      "attributes": "Ti,AA.AuId,AA.AuN,AA.AfN,AA.AfId,L,Y,D,CC,ECC,F.FN,C.CN,C.CId,J.JId,J.JN"
      # "attributes": "prob,Id,Ti,Y,CC,AA.AuN,AA.AuId,RId"
    }

    data = query_academic_search("get", url, query)
    return data["entities"]

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

def get_morepaperinfo_from_title(paper_title):
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/interpret")
    data = query_academic_search("get", url, {"query": paper_title})
    # print(data)
    interpret_expr = data["interpretations"][0]["rules"][0]["output"]["value"]
    # print(interpret_expr)
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    query = {
      "expr": interpret_expr,
      "count": 1000,
      "attributes": "Id,Ti,Y,D,CC,ECC,AA.AuN,AA.AuId,AA.AfN,AA.AfId,F.FN,F.FId,J.JN,J.JId,C.CN,C.CId"
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


def get_papers_from_entity_names(entity_names, entityType):
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    base_string = "Composite("+entity_search_details[entityType]['link_to_paper']+"={})"
    or_string = or_query_builder(base_string, entity_names)
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



def get_papers_from_entity_ids(entity_ids, entity_type):
    entity_type_helper_dict = {'author': 'AA.AuId', 'affiliation': 'AA.AfId', 'journal': 'J.JId', 'conference': 'C.CId'}
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    base_string = "Composite("+entity_type_helper_dict[entity_type]+"={})"
    or_string = or_query_builder(base_string, entity_ids)
    expr = "{}".format(or_string)
    query = lambda expression, count, offset: {
      "expr": expression,
      "count": count,
      "offset": offset,
      "attributes": "Id"
    }

    data = []
    offset = 0
    count = 1000
    continue_querying = True
    while continue_querying:
        print(query(expr, count,offset))
        new_data =  query_academic_search("get", url, query(expr, count, offset))['entities']
        data += new_data
        if len(new_data) < 1000:
            continue_querying = False
        else:
            offset += count
    data = [paper['Id'] for paper in data]
    print(data)
    print(len(data))
    return data

def get_papers_from_author_ids(entity_ids):
    return get_papers_from_entity_ids(entity_ids, 'author')

def get_papers_from_affiliation_ids(entity_ids):
    return get_papers_from_entity_ids(entity_ids, 'affiliation')

def get_papers_from_journal_ids(entity_ids):
    return get_papers_from_entity_ids(entity_ids, 'journal')

def get_papers_from_conference_ids(entity_ids):
    return get_papers_from_entity_ids(entity_ids, 'conference')


def get_entities_from_search(keyword, entityType):
  data = get_morepaperinfo_from_title(keyword) if entityType == "paper"  else get_search_results(keyword, entityType)
  print('\n\n\n\n\n\n\n\n')
  print(data)
  print('\n\n\n\n\n\n\n\n\n')
  data = parse_search_results(data, entityType)
  print(data)

  if entityType in ['author', 'conference', 'institution', 'journal']:
      eids = [entity['eid'] for entity in data]
      papers = get_papers_from_entity_names(eids, entityType)
      # print(papers['entities'][0])
      papers = parse_search_results(papers, 'paper')
      data = link_papers_to_entities(papers, data, entityType)
      data = [x for x in data.values()]

  for entity in data:
      entity['entity-type'] = entityType
  return data

def get_names_from_author_ids(author_ids):
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    base_string = "Id={}"
    or_string = or_query_builder(base_string, author_ids)
    expr = "{}".format(or_string)
    query = {
      "expr": expr,
      "count": 1000,
      "offset": 0,
      "attributes": "AuN"
    }
    data = query_academic_search("get", url, query)
    data = list(set([res["AuN"] for res in data["entities"]]))
    return data

def printDict(d):
    print("dict():")
    for k,v in d.items():
        if k == 'papers':
            v = v[:1]
        print("\t{}\t{}".format(k,v))
