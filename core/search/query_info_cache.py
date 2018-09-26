'''
Functions for querying database for cache information.

date:   24.06.18
author: Alexander Soen
'''
from datetime import datetime

from graph.config import conf
from core.search.query_utility import field_del
from core.search.query_utility import chunker

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search


DEFAULT_BATCH = 1000


#def paper_info_cache_query(paper_ids, batch_size=DEFAULT_BATCH):
#    ''' Gets paper info from cache.
#    '''
#    # Elastic search client
#    client = Elasticsearch(conf.get("elasticsearch.hostname"))
#
#    # Query results
#    complete_info = list()
#    partial_info  = list()
#    seen = set()
#
#    for paper_chunk in chunker(paper_ids, batch_size=batch_size):
#        
#        # Query for paper info
#        paper_info_s = client.mget(index='paper_info', doc_type='doc', body={"ids": paper_chunk})
#
#        # Convert query into dictionary format
#        for paper_info in paper_info_s['docs']: #paper_info_s.scan():
#            #paper_info_res = paper_info.to_dict()
#            paper_info_res = paper_info['_source']
#
#            # Remove the creation date for query
#            field_del(paper_info_res, 'CreatedDate')
#
#            # Check the type of the result
#            if paper_info_res['cache_type'] == 'partial':
#                partial_info.append(paper_info_res)
#            else:
#                complete_info.append(paper_info_res)
#
#            del paper_info_res['cache_type']
#
#            # Add to seen set
#            seen.add(paper_info_res['PaperId'])
#
#    # Check for no results and return
#    return {'complete': complete_info, 'partial': partial_info,
#            'missing': set(paper_ids) - seen}
#

def paper_info_cache_query(paper_ids, batch_size=DEFAULT_BATCH):
    ''' Gets paper info from cache.
    '''
    start = datetime.now()

    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Query results
    complete_info = list()
    partial_info  = list()
    seen = set()

    # Query for paper info
    paper_info_s = Search(index = 'paper_info', using = client)
    paper_info_s = paper_info_s.filter('terms', _id = paper_ids)
    paper_info_s = paper_info_s.params(size=DEFAULT_BATCH)

    # Convert query into dictionary format
    for paper_info in paper_info_s.scan():
        paper_info_res = paper_info.to_dict()

        # Remove the creation date for query
        field_del(paper_info_res, 'CreatedDate')

        # Check the type of the result
        if paper_info_res['cache_type'] == 'partial':
            partial_info.append(paper_info_res)
        else:
            complete_info.append(paper_info_res)

        del paper_info_res['cache_type']

        # Add to seen set
        seen.add(paper_info_res['PaperId'])

    print(batch_size, datetime.now() - start)

    # Check for no results and return
    return {'complete': complete_info, 'partial': partial_info,
            'missing': set(paper_ids) - seen}


def base_paper_cache_query(paper_ids):
    ''' Gets basic paper information required for reference links from cache.
    '''
    # Get properties
    es_res = paper_info_cache_query(paper_ids)
    es_prop = es_res['complete'] + es_res['partial']

    # If empty results
    if len(es_prop) < 0:
        return None

    # Delete extra fields
    prop_res = list()
    for info in es_prop:
        field_del(info, 'References')
        field_del(info, 'Citations')
        field_del(info, 'cache_type')
        prop_res.append(info)

    return prop_res
