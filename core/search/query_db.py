'''
Functions for querying database for specific information:
  - Author information (Create generator function to query papers?)
  - Paper information

Each query goes through a cache layer before presenting information.
Without Pandas.

date:   24.06.18
author: Alexander Soen
'''

from graph.config import conf
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from core.search.query_cache import base_paper_cache_query

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


def base_paper_db_query(paper_id):
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
                link_paper_prop = base_paper_cache_query(link_paper)
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


def author_paper_query(author_id):
    ''' Query author id for availible papers.
    '''
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Target
    paa_target = 'PaperId'

    # Query results
    auth_paper_res = list()

    # Query for paa
    paa_s = Search(index = 'paperauthoraffiliations', using = client)
    paa_s = paa_s.query('match', AuthorId = author_id)
    paa_s = paa_s.source([paa_target])
    
    # Parse to list
    for paa in paa_s.scan():
        auth_paper_res.append(paa[paa_target])

    return auth_paper_res


def affiliation_paper_query(affi_id):
    ''' Query affiliation id for availible papers.
    '''
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Target
    paa_target = 'PaperId'

    # Query results
    affi_paper_res = list()

    # Query for paa
    paa_s = Search(index = 'paperauthoraffiliations', using = client)
    paa_s = paa_s.query('match',  AffiliationId = affi_id)
    paa_s = paa_s.source([paa_target])
    
    # Parse to list
    for paa in paa_s.scan():
        affi_paper_res.append(paa[paa_target])

    return affi_paper_res


def conference_paper_query(conf_id):
    ''' Query conference (instance) id for availible papers.
    '''
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Target
    papers_target = 'PaperId'

    # Query results
    conf_paper_res = list()

    # Query for papers
    papers_s = Search(index = 'papers', using = client)
    papers_s = papers_s.query('match', ConferenceInstanceId = conf_id)
    papers_s = papers_s.source([papers_target])

    # Parse to list
    for papers in papers_s.scan():
        conf_paper_res.append(papers[papers_target])

    return conf_paper_res


def journal_paper_query(jour_id):
    ''' Query journal id for availible papers.
    '''
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Target
    papers_target = 'PaperId'

    # Query results
    jour_paper_res = list()

    # Query for papers
    papers_s = Search(index = 'papers', using = client)
    papers_s = papers_s.query('match', JournalId = jour_id)
    papers_s = papers_s.source([papers_target])

    # Parse to list
    for papers in papers_s.scan():
        jour_paper_res.append(papers[papers_target])

    return jour_paper_res


if __name__ == '__main__':
    # TESTING
    print(author_paper_query(1565612411))
    print(conference_paper_query(2793938785))
    print(journal_paper_query(148324379))
    print(affiliation_paper_query(219193219))






    #from core.search.query_db import author_name_db_query
    #from elasticsearch import helpers
    #from core.search.query_utility import paper_info_to_cache_json
    #from core.search.query_cache import paper_info_cache_query

    #author_df = author_name_db_query('antony l hosking')

    #a_papers = list(author_df['PaperId'])
    #cache_json = list()

    #for paper in a_papers:
    #    paper_info_cache_query(paper)

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
