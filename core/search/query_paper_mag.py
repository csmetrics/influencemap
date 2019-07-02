'''
Functions for querying database for papers from entity ids with the MAG API.

date:   25.06.18
author: Alexander Soen
'''

from core.config import *
from core.search.mag_interface import *
from core.utils.entity_type import Entity_type
from core.search.parse_academic_search import or_query_builder

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

    data = query_academic_search('post', url, query)

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

    data = query_academic_search('post', url, query)

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

    data = query_academic_search('post', url, query)

    # Query result
    conf_id = int()

    for res in data['entities']:
        # Set name
        conf_id = res['PCS']['CId']

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

    data = query_academic_search('post', url, query)

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

    data = query_academic_search('post', url, query)

    # Query result
    papers = list()

    for res in data['entities']:
        # Set name
        papers.append(res['Id'])

    return papers


def paper_mag_query(entity_type, entity_name):
    ''' Query entity id for papers depending on type.
    '''
    # Call query functions depending on type given
    # Author
    if entity_type == Entity_type.AUTH:
        return author_paper_mag_query(entity_name)

    # Affiliation
    if entity_type == Entity_type.AFFI:
        return affiliation_paper_mag_query(entity_name)

    # Conference
    if entity_type == Entity_type.CONF:
        return conference_paper_mag_query(entity_name)

    # Journal
    if entity_type == Entity_type.JOUR:
        return journal_paper_mag_query(entity_name)

    # Otherwise
    return None

def author_paper_mag_multiquery(author_ids):
    ''' Find author name from id.
    '''
    # Query
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    queries = lambda x: {
        'expr': or_query_builder('Composite(AA.AuId={})', author_ids),
        'count': 1000,
        'offset': x,
        'attributes': 'AA.AuId'
        }

    # Query result
    papers = list()

    # Checking offsets
    finished = False
    count    = 0

    while not finished:
        data = query_academic_search('post', url, queries(count))

        # Check if no more data
        if len(data['entities']) > 0:
            count += len(data['entities'])
        else:
            finished = True

        for res in data['entities']:
            # Set name
            papers.append(res['Id'])

    return papers


def affiliation_paper_mag_multiquery(affiliation_ids):
    ''' Find affiliation name from id.
    '''
    # Query
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    query = lambda x: {
        'expr': or_query_builder('Composite(AA.AfId={})', affiliation_ids),
        'count': 10000,
        'offset': x,
        'attributes': 'Id'
        }

    # Query result
    papers = list()

    # Checking offsets
    finished = False
    count    = 0

    while not finished:
        data = query_academic_search('post', url, query(count))

        # Check if no more data
        if len(data['entities']) > 0:
            count += len(data['entities'])
        else:
            finished = True

        for res in data['entities']:
            # Set name
            papers.append(res['Id'])

    return papers


def conference_paper_mag_multiquery(conference_ids):
    ''' Find conference series name from id.
    '''
    # Query
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    query = lambda x: {
        'expr': or_query_builder('Composite(C.CId={})', conference_ids),
        'count': 10000,
        'offset': x,
        'attributes': 'Id'
        }

    # Query result
    papers = list()

    # Checking offsets
    finished = False
    count    = 0

    while not finished:
        data = query_academic_search('post', url, query(count))

        # Check if no more data
        if len(data['entities']) > 0:
            count += len(data['entities'])
        else:
            finished = True

        for res in data['entities']:
            # Set name
            papers.append(res['Id'])

    return papers


def journal_paper_mag_multiquery(journal_ids):
    ''' Find journal name from id.
    '''
    # Query
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    query = lambda x: {
        'expr': or_query_builder('Composite(J.JId={})', journal_ids),
        'count': 10000,
        'offset': x,
        'attributes': 'Id'
        }

    # Query result
    papers = list()

    # Checking offsets
    finished = False
    count    = 0

    while not finished:
        data = query_academic_search('post', url, query(count))

        # Check if no more data
        if len(data['entities']) > 0:
            count += len(data['entities'])
        else:
            finished = True

    for res in data['entities']:
        # Set name
        papers.append(res['Id'])

    return papers


def paper_mag_multiquery(entity_type, entity_names):
    ''' Query entity id for papers depending on type.
    '''
    # Call query functions depending on type given
    # Author
    if entity_type == Entity_type.AUTH:
        return author_paper_mag_multiquery(entity_names)

    # Affiliation
    if entity_type == Entity_type.AFFI:
        return affiliation_paper_mag_multiquery(entity_names)

    # Conference
    if entity_type == Entity_type.CONF:
        return conference_paper_mag_multiquery(entity_names)

    # Journal
    if entity_type == Entity_type.JOUR:
        return journal_paper_mag_multiquery(entity_names)

    # Otherwise
    return None


if __name__ == '__main__':
    author_paper_mag_query(2100918400)
