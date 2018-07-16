'''
Functions for querying database for cache information.

date:   24.06.18
author: Alexander Soen
'''

from graph.config import conf
from core.search.query_utility import field_del

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search


def paper_info_cache_query(paper_id):
    ''' Gets paper info from cache.
    '''
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Query results
    paper_info_res = dict()

    # Query for paper info
    paper_info_s = Search(index = 'paper_info', using = client)
    paper_info_s = paper_info_s.query('match', PaperId = paper_id)

    # Convert query into dictionary format
    for paper_info in paper_info_s.scan():
        paper_info_res = paper_info.to_dict()

        # Remove the creation date for query
        field_del(paper_info_res, 'CreatedDate')

        # Should only be a single result
        break

    # Check for no results and return
    return paper_info_res if paper_info_res else None


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
