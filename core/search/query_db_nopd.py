'''
Functions for querying database for specific information:
  - Author information (Create generator function to query papers?)
  - Paper information

Each query goes through a cache layer before presenting information.
Without Pandas.

date:   19.06.18
author: Alexander Soen
'''

from graph.config import conf
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from itertools import groupby
from datetime import datetime

get_paper_id = lambda x: x['PaperId']

def papers_prop_query(paper_id):
    ''' Get properties of a paper.
    '''
    
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Targets
    papers_targets = ['PaperId', 'ConferenceInstanceId', 'JournalId', 'Year']

    # Query results
    papers_res = dict()

    # Query for papers
    papers_s = Search(index = 'papers', using = client)
    papers_s = papers_s.query('match', PaperId = paper_id)
    papers_s = papers_s.source(papers_targets)

    # Convert papers into dictionary format
    for paper in papers_s.scan():
        # Parse results to dictionaries
        for target in papers_targets:
            try:
                papers_res[target] = paper[target]
            except KeyError:
                pass

        # There only should be a single results per paper id
        break

    # Check for no results and return
    return papers_res if papers_res else None


def paa_prop_query(paper_id):
    ''' Get properties of a paper.
    '''
    
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Targets
    paa_targets = ['AuthorId', 'AffiliationId']

    # Query results
    paa_list = list()

    # Query for paper affiliation
    paa_s = Search(index = 'paperauthoraffiliations', using = client)
    paa_s = paa_s.query('match', PaperId = paper_id)
    paa_s = paa_s.source(paa_targets)

    # Convert paa into dictionary format
    for paa in paa_s.scan():
        row_dict = dict()

        # Parse results to dictionaries
        for target in paa_targets:
            try:
                row_dict[target] = paa[target]
            except KeyError:
                pass

        # Add to query list
        paa_list.append(row_dict)

    # Return as dictionary
    return {'Authors': paa_list}
    

def pr_links_query(paper_id):
    ''' Get properties of a paper.
    '''
    
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Targets
    pr_targets = ['PaperId', 'PaperReferenceId']

    # Query results
    references = list()
    citations  = list()

    # Query for paper references
    pref_s = Search(index = 'paperreferences', using = client)
    pref_s = pref_s.query('multi_match', query = paper_id, fields = pr_targets)

    # Convert into dictionary format
    for cite_info in pref_s.scan():

        # Determine what type of citation
        if paper_id == cite_info[pr_targets[0]]:
            citations.append(cite_info[pr_targets[1]])
        else:
            references.append(cite_info[pr_targets[0]])

    # Return results as a dictionary
    return {'References': references, 'Citations': citations}


def base_paper_info_query(paper_id):
    ''' Generates basic paper_info dictionary/json from basic databases (not
        cache).
    '''
    # Get paper ids
    papers_prop = papers_prop_query(paper_id)

    # Check for empty results
    if not papers_prop:
        return None

    # Get author information
    paa_prop = paa_prop_query(paper_id)

    # Combine results for the basic paper information
    return dict(papers_prop, **paa_prop)


def link_paper_info_query(paper_id):
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
            # TODO Check cache first
            link_paper_prop = base_paper_info_query(link_paper)

            # Check if query has result
            if link_paper_prop:
                link_res[link_type].append(link_paper_prop)

        # Return results
        return link_res


def paper_info_db_query(paper_id):
    ''' Generate paper info dictionary/json from base databases (not cache).
    '''
    # Query basic properties
    paper_info = base_paper_info_query(paper_id)

    # Check if result is empty
    if not paper_info:
        return None

    # Add citation link information
    paper_info.update(link_paper_info_query(paper_id))
    
    # Return paper_info
    return paper_info


def paper_info_to_cache_json(paper_info):
    ''' Cache a paper_info dictionary.
    '''
    # Setup meta data
    meta_json = dict()
    meta_json['_id']    = paper_info['PaperId']
    meta_json['_index'] = 'paper_info'
    meta_json['_type']  = 'doc'

    # Source data
    source = paper_info
    source['CreatedDate'] = datetime.now()

    # Return join of data
    meta_json['_source'] = source
    return meta_json

if __name__ == '__main__':
    # TESTING
    from core.search.query_db import author_name_db_query
    from elasticsearch import helpers
    author_df = author_name_db_query('antony l hosking')

    a_papers = list(author_df['PaperId'])
    cache_json = list()
    for paper in a_papers:
        print(paper)
        paper_info = paper_info_db_query(paper)
        if paper_info:
            cache_json.append(paper_info_to_cache_json(paper_info))
        print('---\n')

    client = Elasticsearch(conf.get("elasticsearch.hostname"))
    helpers.bulk(client, cache_json)
