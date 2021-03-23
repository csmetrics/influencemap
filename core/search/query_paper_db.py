'''
Functions for querying database for papers from entity ids.

date:   24.06.18
author: Alexander Soen
'''

from core.elastic import client
from core.utils.entity_type import Entity_type

from elasticsearch_dsl import Search

def author_paper_query(author_ids):
    ''' Query author id for availible papers.
    '''
    # Target
    paa_target = 'PaperId'

    # Query results
    auth_paper_res = list()

    # Query for paa
    paa_s = Search(index = 'paperauthoraffiliations', using = client)
    paa_s = paa_s.query('terms', AuthorId=author_ids)
    paa_s = paa_s.source([paa_target])

    # Parse to list
    for paa in paa_s.scan():
        auth_paper_res.append(paa[paa_target])

    return auth_paper_res


def affiliation_paper_query(affi_ids):
    ''' Query affiliation id for availible papers.
    '''
    # Target
    paa_target = 'PaperId'

    # Query results
    affi_paper_res = list()

    # Query for paa
    paa_s = Search(index = 'paperauthoraffiliations', using = client)
    paa_s = paa_s.query('terms',  AffiliationId=affi_ids)
    paa_s = paa_s.source([paa_target])

    # Parse to list
    for paa in paa_s.scan():
        affi_paper_res.append(paa[paa_target])

    return affi_paper_res


def conference_paper_query(conf_ids):
    ''' Query conference (instance) id for availible papers.
    '''
    # Target
    papers_target = 'PaperId'

    # Query results
    conf_paper_res = list()

    # Query for papers
    papers_s = Search(index = 'papers', using = client)
    papers_s = papers_s.query('terms', ConferenceSeriesId=conf_ids)
    papers_s = papers_s.source([papers_target])
    papers_s = papers_s.params(request_timeout=30)

    # Parse to list
    for papers in papers_s.scan():
        conf_paper_res.append(papers[papers_target])

    return conf_paper_res


def journal_paper_query(jour_ids):
    ''' Query journal id for availible papers.
    '''
    # Target
    papers_target = 'PaperId'

    # Query results
    jour_paper_res = list()

    # Query for papers
    papers_s = Search(index = 'papers', using = client)
    papers_s = papers_s.query('terms', JournalId=jour_ids)
    papers_s = papers_s.source([papers_target])
    papers_s = papers_s.params(request_timeout=30)

    # Parse to list
    for papers in papers_s.scan():
        jour_paper_res.append(papers[papers_target])

    return jour_paper_res


def paper_query(entity_type, entity_ids):
    ''' Query entity id for papers depending on type.
    '''
    # Call query functions depending on type given
    # Author
    if entity_type == Entity_type.AUTH:
        return author_paper_query(entity_ids)

    # Affiliation
    if entity_type == Entity_type.AFFI:
        return affiliation_paper_query(entity_ids)

    # Conference
    if entity_type == Entity_type.CONF:
        return conference_paper_query(entity_ids)

    # Journal
    if entity_type == Entity_type.JOUR:
        return journal_paper_query(entity_ids)

    # Field of Study
    if entity_type == Entity_type.FSTD:
        pass

    # Otherwise
    return None


if __name__ == '__main__':
    # TESTING
    #print(author_paper_query(1565612411))
    #print(conference_paper_query(2793938785))
    #print(journal_paper_query(148324379))
    #print(affiliation_paper_query(219193219))
    print()
