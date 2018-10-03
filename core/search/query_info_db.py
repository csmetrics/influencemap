'''
Functions for querying database for specific information:
  - Author information (Create generator function to query papers?)
  - Paper information

Each query goes through a cache layer before presenting information.
Without Pandas.

date:   24.06.18
author: Alexander Soen
'''

import copy
from datetime import datetime

from graph.config import conf
from core.search.query_info_cache import base_paper_cache_query

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q

TIMEOUT = 60

def papers_prop_query(paper_ids):
    ''' Get properties of a paper.
    '''
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Targets
    papers_targets = ['ConferenceInstanceId', 'JournalId', 'Year']

    # Query for papers
    papers_s = Search(index = 'papers', using = client)
    papers_s = papers_s.query('terms', _id=paper_ids)
    papers_s = papers_s.source(papers_targets)
    papers_s = papers_s.params(request_timeout=TIMEOUT)

    # Convert papers into dictionary format
    results = dict()
    for paper in papers_s.scan():
        # Get properties for papers
        paper_res = paper.to_dict()
        p_id = int(paper.meta.id)

        # Rename Conference
        if 'ConferenceInstanceId' in paper_res:
            paper_res['ConferenceId'] = paper_res.pop('ConferenceInstanceId')

        paper_res['PaperId'] = p_id
        results[p_id] = paper_res

    return results


def paa_prop_query(paper_ids):
    ''' Get properties of a paper.
    '''
    
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Targets
    paa_targets = ['PaperId', 'AuthorId', 'AffiliationId']

    # Query for paper affiliation
    paa_s = Search(index = 'paperauthoraffiliations', using = client)
    paa_s = paa_s.query('terms', PaperId=paper_ids)
    paa_s = paa_s.source(paa_targets)
    paa_s = paa_s.params(request_timeout=TIMEOUT)

    # Convert paa into dictionary format
    results = dict()
    for paa in paa_s.scan():
        paa_res = paa.to_dict()

        # Get fields
        paper_id = paa_res['PaperId']
        del paa_res['PaperId']

        # Aggregate results
        if paper_id in results:
            results[paper_id].append(paa_res)
        else:
            results[paper_id] = [paa_res]

    # Return as dictionary
    return results
    

def pr_links_query(paper_ids):
    ''' Get properties of a paper.
    '''
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Targets
    pr_targets = ['PaperId', 'PaperReferenceId']

    # Query results
    references = list()
    citations  = list()

    # Result dictionary
    results = dict()
    for paper_id in paper_ids:
        results[paper_id] = {'References': [], 'Citations': []}

    # Query for paper references
    ref_s = Search(index = 'paperreferences', using = client)
    ref_s = ref_s.query('terms', PaperId=paper_ids)
    ref_s = ref_s.params(request_timeout=TIMEOUT)

    # Convert into dictionary format
    for ref_info in ref_s.scan():
        results[ref_info[pr_targets[0]]]['References'].append(ref_info[pr_targets[1]])

    # Query for paper citations
    cit_s = Search(index = 'paperreferences', using = client)
    cit_s = cit_s.query('terms', PaperReferenceId=paper_ids)
    cit_s = cit_s.params(request_timeout=TIMEOUT)

    # Convert into dictionary format
    for cit_info in cit_s.scan():
        results[cit_info[pr_targets[1]]]['Citations'].append(cit_info[pr_targets[0]])

    # Return results as a dictionary
    return results


def base_paper_db_query(paper_ids):
    ''' Generates basic paper_info dictionary/json from basic databases (not
        cache).
    '''
    t_cur = datetime.now()
    # Get basic paper properties
    papers_props = papers_prop_query(paper_ids)
    print('Get basic props', datetime.now() - t_cur)


    t_cur = datetime.now()
    # Get author information
    paa_props = paa_prop_query(paper_ids)
    print('Get paa', datetime.now() - t_cur)

    # Create partial entry
    results = list()
    for paper_id in paper_ids:
        if paper_id in papers_props and paper_id in paa_props:
            # Make partial result
            partial_res = papers_props[paper_id]
            partial_res['Authors'] = paa_props[paper_id]

            results.append(partial_res)

    return results


def link_paper_info_query(paper_id, cache = True):
    ''' Gets the basic paper information required for the links.
    '''
    # Get citation links
    pr_links = pr_links_query(paper_id)

    # Query results
    link_res = dict()

    # Iterate through the link types
    for link_type, link_papers in pr_links.items():

        # Resulting link results
        link_res[link_type] = list()

        # Iterate through the papers
        for link_paper in link_papers:

            # If cache true
            if cache:
                # Check cache for entries
                link_paper_prop = base_paper_cache_query([link_paper])[0]
            else:
                # Set default to None
                link_paper_prop = None
            
            # If empty result
            if not link_paper_prop:
                # Do full search
                link_paper_prop = base_paper_db_query(link_paper)

            # Check if query has result
            if link_paper_prop:
                link_res[link_type].append(link_paper_prop)

    # Return results
    return link_res


def paper_info_db_query(paper_id):
    ''' Generate paper info dictionary/json from base databases (not cache).
    '''
    # Query basic properties
    paper_info = base_paper_db_query(paper_id)

    # Check if result is empty
    if not paper_info:
        return None

    # Add citation link information
    paper_info.update(link_paper_info_query(paper_id))
    
    # Return paper_info
    return paper_info


def paper_info_multiquery(paper_ids, partial_info=list()):
    '''
    '''
    # Create partial information dictionary
    paper_partial = dict()
    for p_info in partial_info:
        paper_partial[p_info['PaperId']] = p_info

    # List of papers we are interested in returning total results
    search_papers = paper_ids + list(paper_partial.keys())
    
    t_cur = datetime.now()
    # Find all paper links
    paper_links = pr_links_query(search_papers)
    print('Get links', datetime.now() - t_cur)

    # Calculate papers to query es for partials
    find_partial = set(paper_ids)
    for paper_link in paper_links.values():
        find_partial.update(paper_link['References'])
        find_partial.update(paper_link['Citations'])

    print("Need to find,", len(find_partial))

    # Get partial information for papers from cache
    for p_info in base_paper_cache_query(list(find_partial)):
        p_id = p_info['PaperId']
        find_partial.remove(p_id)
        paper_partial[p_id] = p_info

    # Get partial information from db
    for p_info in base_paper_db_query(list(find_partial)):
        #print(p_info)
        p_id = p_info['PaperId']
        find_partial.remove(p_id)
        paper_partial[p_id] = p_info

    # Handle infos which cannot be found here TODO
    print(find_partial)
    print('Missing from db', len(find_partial))
    for p_id in find_partial:
        paper_partial[p_id] = {'PaperId': p_id, 'Year': 2018, 'Authors': []}
    
    # Generate results
    total_res   = list()
    partial_res = list()
    for p_id, p_partial in paper_partial.items():

        # TEMP FOR INCOMPLETE
        if p_id in find_partial:
            continue

        p_partial = copy.deepcopy(p_partial)

        # If links exists and is a search paper
        if p_id in search_papers and p_id in paper_links:
            p_partial['cache_type'] = 'complete'

            # Create references and citations for total paper
            p_links = {'References': [], 'Citations': []}

            for r_id in paper_links[p_id]['References']:
                p_links['References'].append(paper_partial[r_id])
                if r_id in find_partial:
                    p_partial['cache_type'] = 'taint'

            for c_id in paper_links[p_id]['Citations']:
                p_links['Citations'].append(paper_partial[c_id])
                if c_id in find_partial:
                    p_partial['cache_type'] = 'taint'

            total_res.append(dict(p_partial, **p_links))
        # Otherwise just add as partial cache entry
        else:
            p_partial['cache_type'] = 'partial'
            partial_res.append(p_partial)

    return total_res, partial_res 


if __name__ == '__main__':
    from core.search.query_db import author_name_db_query
    from elasticsearch import helpers
    from core.search.query_utility import paper_info_to_cache_json
    from core.search.query_cache import paper_info_cache_query

    author_df = author_name_db_query('antony l hosking')

    a_papers = list(author_df['PaperId'])
    cache_json = list()

    for paper in a_papers:
        paper_info_cache_query(paper)

'''
    for paper in a_papers:
        print(paper)
        paper_info = paper_info_db_query(paper)
        if paper_info:
            cache_json.append(paper_info_to_cache_json(paper_info))
        print('---\n')

    client = Elasticsearch(conf.get("elasticsearch.hostname"))
    helpers.bulk(client, cache_json)
'''
