from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

client = Elasticsearch("130.56.248.105:9200")

def search_cache(cache_index, cache_type):
    s = Search(using=client, index=cache_index).query("match", Type=cache_type)
    response = s.execute()
    return response.to_dict()["hits"]["hits"]
