'''
Functions for caching data into elasticsearch database.

date:   24.06.18
author: Alexander Soen
'''

from graph.config import conf
from elasticsearch import Elasticsearch, helpers
from elasticsearch_dsl import Search
from core.search.query_utility import paper_info_to_cache_json

def cache_paper_info(paper_infos):
    ''' Converts and caches a single paper info dictionary.
    '''
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Convert into cache-able json
    cache_datas = (paper_info_to_cache_json(pi) for pi in paper_infos)

    # Cache to database
    helpers.bulk(client, cache_datas)
