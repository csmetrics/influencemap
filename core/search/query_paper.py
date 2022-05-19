from core.search.elastic import client
from core.utils.entity_type import Entity_type
from elasticsearch_dsl import Search
from graph.config import conf


def author_paper_query(author_ids):
    ''' Query author id for availible papers.
    '''
    # Target
    paa_target = 'PaperId'

    # Query results
    auth_paper_res = list()

    # Query for paa
    paa_s = Search(index = conf.get('index.paa'), using = client)
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
    paa_s = Search(index = conf.get('index.paa'), using = client)
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
    papers_s = Search(index = conf.get('index.paper'), using = client)
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
    papers_s = Search(index = conf.get('index.paper'), using = client)
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

    # Otherwise
    return None


def get_all_paper_ids(entity_dict):

    paper_ids = entity_dict['PaperIds'] if "PaperIds" in entity_dict else []

    if "AuthorIds" in entity_dict and entity_dict["AuthorIds"]:
        paper_ids += paper_query(
            Entity_type.AUTH, entity_dict['AuthorIds'])

    if "ConferenceIds" in entity_dict and entity_dict["ConferenceIds"]:
        paper_ids += paper_query(
            Entity_type.CONF, entity_dict['ConferenceIds'])

    if "AffiliationIds" in entity_dict and entity_dict["AffiliationIds"]:
        paper_ids += paper_query(
            Entity_type.AFFI, entity_dict['AffiliationIds'])

    if "JournalIds" in entity_dict and entity_dict["JournalIds"]:
        paper_ids += paper_query(
            Entity_type.JOUR, entity_dict['JournalIds'])

    return paper_ids

if __name__ == "__main__":
    from core.utils.entity_type import Entity_type
    from core.search.academic_search import get_papers_from_entity_ids

    test2 = qp_db.paper_query(Entity_type.AUTH, [2100918400])
