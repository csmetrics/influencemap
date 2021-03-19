'''
Functions which try and get citation links in a variety of ways. For testing
the coverage of the API.

date:   01.07.18
author: Alexander Soen
'''

from core.config                       import *
from core.search.mag_interface         import *
from core.search.query_info_mag        import pr_links_mag_multiquery
from core.search.parse_academic_search import or_query_builder_list

MAS_URL_PREFIX = "https://api.labs.cognitive.microsoft.com"

def link_from_graph(paper_ids):
    ''' Getting links using the graph search API.
    '''
    # Query
    query = {
        'path': '/paper',
        'paper': {
            'type': 'Paper',
            'id': paper_ids,
            'select': ['ReferenceIDs', 'CitationIDs'],
            }
        }

    # Query results
    results = dict()

    # Initalise results
    for paper_id in paper_ids:
        results[paper_id] = {'References': list(), 'Citations': list()}
        
    # Call to API
    data = query_academic_search('post', JSON_URL, query)

    # Add references and citations to results
    for row in data['Results']:
        vals = row[0]
        results[vals['CellID']]['References'] += vals['ReferenceIDs']
        results[vals['CellID']]['Citations']  += vals['CitationIDs']

    return results


def link_from_evaluate(paper_ids):
    ''' Getting links using the evaluate search API.
    '''
    # Query results
    results = dict()

    # Initalise results
    for paper_id in paper_ids:
        results[paper_id] = {'References': list(), 'Citations': list()}

    # Calculate references
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    queries = ({
        'expr': expr,
        'count': 10000,
        'offset': 0,
        'attributes': 'RId'
        } for expr in or_query_builder_list('Id={}', paper_ids))

    for query in queries:
        data = query_academic_search('get', url, query)

        # Add references
        for res in data['entities']:
            if 'RId' in res:
                results[res['Id']]['References'] += res['RId']

    for paper_id in paper_ids:
        query = {
        'expr': 'RId={}'.format(paper_id),
        'count': 10000,
        'offset': 0,
        'attributes': 'Id,RId'
        }

    #for query in queries:
        data = query_academic_search('get', url, query)

        # Add citations
        for res in data['entities']:
            if 'RId' in res:
                for rid in res['RId']:
                    if rid in paper_ids:
                        results[rid]['Citations'].append(res['Id'])

    return results


def author_link_vals(author_ids):
    ''' Get number of citations from querying citations.
    '''
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    queries = ({
        'expr': expr,
        'count': 10000,
        'offset': 0,
        'attributes': 'CC'
        } for expr in or_query_builder_list('Id={}', author_ids))

    # Query results
    results = dict()
    
    for query in queries:
        data = query_academic_search('get', url, query)

        for res in data['entities']:
            try:
                results[res['Id']] = res['CC']
            except KeyError:
                pass

    return results
