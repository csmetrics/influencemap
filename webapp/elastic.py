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

def query_browse_group(document_id):
    result = {}
    cache_index = "browse_cache"
    q = {"query": {"match": {"_id": document_id}}}
    s = Search(using=client, index=cache_index)
    s.update_from_dict(q)
    response = s.execute()
    data = response.to_dict()["hits"]["hits"]
    document = data[0]["_source"]
    return document

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


def get_names_from_entity(entity_ids, index, id_field, name_field):
    result = []
    q = {
      "_source": name_field,
      "size": 100,
      "query": {
        "terms": {id_field : entity_ids}
      }
    }
    s = Search(using=client, index=index)
    s.update_from_dict(q)
    response = s.execute()
    data = response.to_dict()["hits"]["hits"]
    paper_ids = [res["_source"][name_field] for res in data]
    return paper_ids


def get_names_from_conference_ids(entity_ids):
    return get_names_from_entity(entity_ids, "conferenceseries", "ConferenceSeriesId", "NormalizedName")

def get_names_from_affiliation_ids(entity_ids):
    return get_names_from_entity(entity_ids, "affiliations", "AffiliationId", "NormalizedName")

def get_names_from_journal_ids(entity_ids):
    return get_names_from_entity(entity_ids, "journals", "JournalId", "NormalizedName")






