'''
Functions for querying database for cache information.

date:   24.06.18
author: Alexander Soen
'''

from graph.config import conf
from core.search.query_utility import field_del

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search


def paper_info_cache_query(paper_ids):
    ''' Gets paper info from cache.
    '''
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Query results
    complete_info = list()
    partial_info  = list()
    seen = set()

    # Query for paper info
    paper_info_s = Search(index = 'paper_info', using = client)
    paper_info_s = paper_info_s.filter('terms', PaperId = paper_ids)

    # Convert query into dictionary format
    for paper_info in paper_info_s.scan():
        paper_info_res = paper_info.to_dict()

        # Remove the creation date for query
        field_del(paper_info_res, 'CreatedDate')

        # Check the type of the result
        if paper_info['cache_type'] == 'partial':
            partial_info.append(paper_info_res)
        else:
            complete_info.append(paper_info_res)

        del paper_info_res['cache_type']

        # Add to seen set
        seen.add(paper_info_res['PaperId'])

    # Check for no results and return
    return {'complete': complete_info, 'partial': partial_info,
            'missing': set(paper_ids) - seen}


def base_paper_cache_query(paper_id):
    ''' Gets basic paper information required for reference links from cache.
    '''
    # Get properties
    prop_res = paper_info_cache_query(paper_id)

    # Check for empty results
    if not prop_res:
        return None

    # Delete extra fields
    field_del(prop_res, 'References')
    field_del(prop_res, 'Citations')
    field_del(prop_res, 'cache_type')

    return prop_res
