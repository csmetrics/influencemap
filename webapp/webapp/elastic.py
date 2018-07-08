from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from graph.save_cache import generate_uuid
from core.search.query_info_cache import paper_info_cache_query

client = Elasticsearch("130.56.248.105:9200")

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
    response = s.execute()
    return response.to_dict()["hits"]["hits"]

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
