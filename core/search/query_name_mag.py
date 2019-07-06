'''
Functions for querying database for entity names from entity ids from API.

date:   25.06.18
author: Alexander Soen
'''

from core.config import *
from core.search.mag_interface import *
from core.utils.entity_type import Entity_type
from core.search.parse_academic_search import or_query_builder

MAS_URL_PREFIX = "https://api.labs.cognitive.microsoft.com"

def author_name_mag_multiquery(author_ids):
    ''' Find author name from id.
    '''
    # Query
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    query = lambda x: {
        'expr': or_query_builder('Id={}', author_ids),
        'count': 10000,
        'offset': x,
        'attributes': 'AuN'
        }

    # Query result
    auth_name_res = dict()

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
            auth_name_res[res['Id']] = res['AuN']

    print(auth_name_res)

    return auth_name_res


def affiliation_name_mag_multiquery(affiliation_ids):
    ''' Find affiliation name from id.
    '''
    # Query
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    query = lambda x: {
        'expr': or_query_builder('Id={}', affiliation_ids),
        'count': 10000,
        'offset': x,
        'attributes': 'AfN'
        }

    # Query result
    affi_name_res = dict()

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
            affi_name_res[res['Id']] = res['AfN']

    return affi_name_res


def conference_name_mag_multiquery(conference_ids):
    ''' Find conference name from id.
    '''
    # Query
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    query = lambda x: {
        'expr': or_query_builder('Id={}', conference_ids),
        'count': 10000,
        'offset': x,
        'attributes': 'PCS.CN'
        }

    # Query result
    conf_name_res = dict()

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
            try:
                conf_name_res[res['Id']] = res['PCS']['CN']
            except KeyError:
                pass

    # Try Series now
    # Query
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    query = lambda x: {
        'expr': or_query_builder('Id={}', conference_ids),
        'count': 10000,
        'offset': x,
        'attributes': 'CN'
        }

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
            try:
                conf_name_res[res['Id']] = res['CN']
            except KeyError:
                pass

    return conf_name_res


def journal_name_mag_multiquery(journal_ids):
    ''' Find journal name from id.
    '''
    # Query
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    query = lambda x: {
        'expr': or_query_builder('Id={}', journal_ids),
        'count': 10000,
        'offset': x,
        'attributes': 'DJN'
        }

    # Query result
    jour_name_res = dict()

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
            try:
                jour_name_res[res['Id']] = res['DJN']
            except KeyError:
                pass

    return jour_name_res


def name_mag_multiquery(entity_type, entity_names):
    ''' Query entity id for name depending on type.
    '''
    # Call query functions depending on type given
    # Author
    if entity_type == Entity_type.AUTH:
        return author_name_mag_multiquery(entity_names)

    # Affiliation
    if entity_type == Entity_type.AFFI:
        return affiliation_name_mag_multiquery(entity_names)

    # Conference
    if entity_type == Entity_type.CONF:
        return conference_name_mag_multiquery(entity_names)

    # Journal
    if entity_type == Entity_type.JOUR:
        return journal_name_mag_multiquery(entity_names)

    # Otherwise
    return None


if __name__ == '__main__':
    #author_name_mag_query(2100918400)
    print(affiliation_name_mag_multiquery([1334950195]))
