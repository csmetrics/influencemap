'''
Functions for querying database for papers from entity ids with the MAG API.

date:   25.06.18
author: Alexander Soen
'''

from core.config import *
from core.search.mag_interface import *
from core.utils.entity_type import Entity_type

MAS_URL_PREFIX = "https://api.labs.cognitive.microsoft.com"

def author_paper_mag_query(author_id):
    ''' Find author name from id.
    '''
    # Query
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    query = {
        'expr': 'Composite(AA.AuId={})'.format(author_id),
        'count': 100,
        'offset': 0,
        'attributes': 'Id'
        }

    data = query_academic_search('get', url, query)

    # Query result
    papers = list()

    for res in data['entities']:
        # Set name
        papers.append(res['Id'])

    return papers


def affiliation_paper_mag_query(affiliation_id):
    ''' Find affiliation name from id.
    '''
    # Query
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    query = {
        'expr': 'Composite(AA.AfId={})'.format(affiliation_id),
        'count': 100,
        'offset': 0,
        'attributes': 'Id'
        }

    data = query_academic_search('get', url, query)

    # Query result
    papers = list()

    for res in data['entities']:
        # Set name
        papers.append(res['Id'])

    return papers


def conference_instance_to_series_mag(conference_id):
    ''' Find conference instance id to conference series id.
    '''
    # Query
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    query = {
        'expr': 'Id={}'.format(conference_id),
        'count': 1,
        'offset': 0,
        'attributes': 'PCS.CId'
        }

    data = query_academic_search('get', url, query)

    # Query result
    conf_id = int()

    for res in data['entities']:
        # Set name
        conf_id = res['PCS.CId']

        # Should only be one result
        break

    return conf_id


def conference_paper_mag_query(conference_id):
    ''' Find conference name from id.
    '''
    # Turn to series id
    new_id = conference_instance_to_series_mag(conference_id)
    if new_id:
        conference_id = new_id

    # Query
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    query = {
        'expr': 'Composite(C.CId={})'.format(conference_id),
        'count': 100,
        'offset': 0,
        'attributes': 'Id'
        }

    data = query_academic_search('get', url, query)

    # Query result
    papers = list()

    for res in data['entities']:
        # Set name
        papers.append(res['Id'])

    return papers


def journal_paper_mag_query(journal_id):
    ''' Find journal name from id.
    '''
    # Query
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    query = {
        'expr': 'Composite(J.JId={})'.format(journal_id),
        'count': 100,
        'offset': 0,
        'attributes': 'Id'
        }

    data = query_academic_search('get', url, query)

    # Query result
    papers = list()

    for res in data['entities']:
        # Set name
        papers.append(res['Id'])

    return papers


def paper_mag_query(entity_type, entity_id):
    ''' Query entity id for papers depending on type.
    '''
    # Call query functions depending on type given
    # Author
    if entity_type == Entity_type.AUTH:
        return author_paper_mag_query(entity_id)

    # Affiliation
    if entity_type == Entity_type.AFFI:
        return affiliation_paper_mag_query(entity_id)

    # Conference
    if entity_type == Entity_type.CONF:
        return conference_paper_mag_query(entity_id)

    # Journal
    if entity_type == Entity_type.JOUR:
        return journal_paper_mag_query(entity_id)

    # Otherwise
    return None


if __name__ == '__main__':
    author_paper_mag_query(2100918400)
