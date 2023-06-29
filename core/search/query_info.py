'''
Functions which combines the different query functions in query_db and
query_cache.

date:   24.06.18
author: Alexander Soen
'''

from core.search.elastic import client
from core.search.query_name import *

from elasticsearch_dsl import Search, Q
from graph.config import conf

TIMEOUT = 60

def papers_prop_query(paper_ids):
    ''' Get properties of a paper.
    '''
    # Targets
    papers_targets = ['DocType', 'OriginalTitle', 'OriginalVenue', 'Year']

    # Query for papers
    papers_s = Search(index = conf.get('index.paper'), using = client)
    papers_s = papers_s.query('terms', PaperId=paper_ids)
    papers_s = papers_s.source(papers_targets)
    papers_s = papers_s.params(request_timeout=TIMEOUT)

    # Convert papers into dictionary format
    results = dict()
    conf_ids = set()
    jour_ids = set()
    for paper in papers_s.scan():
        # Get properties for papers
        paper_res = paper.to_dict()
        p_id = int(paper.meta.id)
        paper_res['PaperId'] = p_id
        results[p_id] = paper_res

    return results