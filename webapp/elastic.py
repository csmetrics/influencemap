from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from core.search.query_info_cache import paper_info_cache_query
from graph.config import conf

client = Elasticsearch(conf.get("elasticsearch.hostname"))

def query_cache_paper_info(author_id):
    result = {}
    cache_index = "paper_info"
    author_ids = author_id if type(author_id)==list else [author_id]
    q = {"_source": "PaperId",
        "size": 10000,
        "query": {"terms": { "Authors.AuthorId": author_ids}}}
    s = Search(using=client, index=cache_index)
    s.update_from_dict(q)
    response = s.execute()
    data = response.to_dict()["hits"]["hits"]
    # print(data["hits"]["total"])
    paper_ids = [e["_source"]["PaperId"] for e in data]
    return paper_ids

def query_author_group(author_name):
    result = {}
    cache_index = "browse_author_group"
    q = {"_source": "AuthorIds",
        "query": {"match": {"NormalizedNames": author_name}}}
    s = Search(using=client, index=cache_index)
    s.update_from_dict(q)
    response = s.execute()
    data = response.to_dict()["hits"]["hits"]
    author_ids = data[0]["_source"]["AuthorIds"]
    return query_cache_paper_info(author_ids)


def search_cache(cache_index, cache_type):
    s = Search(using=client, index=cache_index).query("match", Type=cache_type)
    response = []
    for res in s.scan():
        res_id = res.meta.id
        res = res.to_dict()
        res["_id"] = res_id
        response.append(res)
    return response

def query_paper_group(document_id):
    result = {}
    cache_index = "browse_paper_group"
    q = {"_source": "PaperIds",
        "query": {"match": {"_id": document_id}}}
    s = Search(using=client, index=cache_index)
    s.update_from_dict(q)
    response = s.execute()
    data = response.to_dict()["hits"]["hits"]
    paper_ids = data[0]["_source"]["PaperIds"]
    return paper_ids


def query_names_with_matches(index, fields_list, search_phrase, max_return=15):
    result = []
    matches = [{"match": {field: search_phrase}} for field in fields_list]
    q = {
        "query":{
          "bool":{
            "should": matches
          }
        }}
    s = Search(using=client, index=index).params(preserve_order=True)
    s.update_from_dict(q)

    count = 0
    for res in s.scan():
        if count >= max_return:
            break
        result.append(res.to_dict())
        count += 1
    return result

def query_conference_series(search_phrase):
    return query_names_with_matches("conferenceseries", ["DisplayName","NormalizedName"] , search_phrase)

def query_journal(search_phrase):
    return query_names_with_matches("journals", ["DisplayName", "NormalizedName"], search_phrase)

def query_affiliation(search_phrase):
    return query_names_with_matches("affiliations", ["DisplayName", "NormalizedName"], search_phrase)

def query_reference_papers(ego_author_ids, node_author_ids):
    result = []
    cache_index = "paper_info"

    print(ego_author_ids, node_author_ids)
    q = {"query":{
           "bool":{
             "must":[
               {"terms": {"Authors.AuthorId": ego_author_ids}},
               {"terms": {"References.Authors.AuthorId": node_author_ids}}
             ]
           }
         }}
    s = Search(using=client, index=cache_index)
    s.update_from_dict(q)
    for res in s.scan():
        result.append(res.to_dict())
    data = result
    data = sorted(data, key = lambda x: len(x["Citations"]), reverse=True)
    #data = [d["_source"]  for d in response.to_dict()["hits"]["hits"]]
    data = [p["PaperId"] for p in data]
    return data

def query_citation_papers(ego_author_ids, node_author_ids):
    result = []
    cache_index = "paper_info"
    q = {"query":{
           "bool":{
             "must":[
               {"terms": {"Authors.AuthorId": ego_author_ids}},
               {"terms": {"Citations.Authors.AuthorId": node_author_ids}}
             ]
           }
         }}
    s = Search(using=client, index=cache_index)
    s.update_from_dict(q)
    for res in s.scan():
        result.append(res.to_dict())
    data = []
    for ego_paper in result:
        for citing_paper in ego_paper["Citations"]:
            for author in citing_paper["Authors"]:
                if author["AuthorId"] in node_author_ids:
                    data.append(citing_paper)
    #data = [d["_source"]  for d in response.to_dict()["hits"]["hits"]]
    data = [p["PaperId"] for p in data]
    return data


def q():

    data = query_referenced_papers([2122328552], [2022407533])
    data = sorted(data, key=lambda x: len(x['Citations']), reverse=True)
    for d in data:
        print(len(d["Citations"]))
    print(data[0].keys())
    print(len(data))





