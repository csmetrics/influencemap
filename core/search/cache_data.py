'''
Functions for caching data into elasticsearch database.

date:   24.06.18
author: Alexander Soen
'''

from graph.config import conf
from elasticsearch import Elasticsearch, helpers
from elasticsearch_dsl import Search
from core.search.query_utility import paper_info_to_cache_json

def cache_paper_info(paper_infos, chunk_size=20):
    ''' Converts and caches a single paper info dictionary.
    '''
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Convert into cache-able json
    paper_info_chunks = [paper_infos[i:i+chunk_size] for i in \
                    range(0, len(paper_infos), chunk_size)]

    # Cache to database
    for chunk in paper_info_chunks:
        cache_datas = (paper_info_to_cache_json(pi) for pi in chunk)
        helpers.bulk(client, cache_datas, refresh=True, stats_only=True)
