'''
Functions for querying database for papers from entity ids.

date:   24.06.18
author: Alexander Soen
'''

from graph.config import conf

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

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
