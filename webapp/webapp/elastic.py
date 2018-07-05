from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

client = Elasticsearch("130.56.248.105:9200")

def query_cache_paper_info(author_id):
    result = {}
    cache_index = "paper_info"
    q = {"_source": "PaperId",
        "size": 10000,
        "query": {"match": { "Authors.AuthorId": author_id}}}
    s = Search(using=client, index=cache_index)
    s.update_from_dict(q)
    response = s.execute()
    data = response.to_dict()["hits"]["hits"]
    # print(data["hits"]["total"])
    paper_ids = [e["_source"]["PaperId"] for e in data]
    return paper_ids


def search_cache(cache_index, cache_type):
    s = Search(using=client, index=cache_index).query("match", Type=cache_type)
    response = s.execute()
    return response.to_dict()["hits"]["hits"]
