'''
Functions for querying database for entity names from entity ids from API.

date:   25.06.18
author: Alexander Soen
'''

from core.config import *
from core.search.mag_interface import *
from core.search.query_name import name_query
from core.utils.entity_type import Entity_type
from core.search.parse_academic_search import or_query_builder_list

MAS_URL_PREFIX = "https://api.labs.cognitive.microsoft.com"

def author_name_mag_multiquery(author_ids):
    ''' Find author name from id.
    '''
    # Query
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    queries = ({
        'expr': expr,
        'count': 10000,
        'offset': 0,
        'attributes': 'AuN'
        } for expr in or_query_builder_list('Id={}', author_ids))

    # Query result
    auth_name_res = dict()

    for query in queries:
        data = query_academic_search('get', url, query)

        for res in data['entities']:
            # Set name
            auth_name_res[res['Id']] = res['AuN']

    return auth_name_res


def affiliation_name_mag_multiquery(affiliation_ids):
    ''' Find affiliation name from id.
    '''
    # Query
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    queries = ({
        'expr': expr,
        'count': 10000,
        'offset': 0,
        'attributes': 'AfN'
        } for expr in or_query_builder_list('Id={}', affiliation_ids))

    # Query result
    affi_name_res = dict()

    for query in queries:
        data = query_academic_search('get', url, query)

        for res in data['entities']:
            # Set name
            affi_name_res[res['Id']] = res['AfN']

    return affi_name_res


def conference_name_mag_multiquery(conference_ids):
    ''' Find conference name from id.
    '''
    # Query
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    queries = ({
        'expr': expr,
        'count': 10000,
        'offset': 0,
        'attributes': 'PCS.CN'
        } for expr in or_query_builder_list('Id={}', conference_ids))

    # Query result
    conf_name_res = dict()

    for query in queries:
        data = query_academic_search('get', url, query)

        for res in data['entities']:
            # Set name
            try:
                conf_name_res[res['Id']] = res['PCS']['CN']
            except KeyError:
                pass

    # Try Series now
    # Query
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    queries = ({
        'expr': expr,
        'count': 10000,
        'offset': 0,
        'attributes': 'CN'
        } for expr in or_query_builder_list('Id={}', conference_ids))

    for query in queries:
        data = query_academic_search('get', url, query)

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
    queries = ({
        'expr': expr,
        'count': 10000,
        'offset': 0,
        'attributes': 'DJN'
        } for expr in or_query_builder_list('Id={}', journal_ids))

    # Query result
    jour_name_res = dict()

    for query in queries:
        data = query_academic_search('get', url, query)

        for res in data['entities']:
            # Set name
            try:
                jour_name_res[res['Id']] = res['DJN']
            except KeyError:
                pass

    return jour_name_res


def name_mag_multiquery(entity_type, entity_ids):
    ''' Query entity id for name depending on type.
    '''
    # Call query functions depending on type given
    # Author
    if entity_type == Entity_type.AUTH:
        return author_name_mag_multiquery(entity_ids)

    # Affiliation
    if entity_type == Entity_type.AFFI:
        return affiliation_name_mag_multiquery(entity_ids)

    # Conference
    if entity_type == Entity_type.CONF:
        return conference_name_mag_multiquery(entity_ids)

    # Journal
    if entity_type == Entity_type.JOUR:
        return journal_name_mag_multiquery(entity_ids)

    # Otherwise
    return None


def name_try_mag_multiquery(entity_type, entity_ids):
    ''' Check ES first, else use the MAG API.
    '''
    to_process = list()
    name_maps  = dict()
    # Try ES
    #for entity_id in entity_ids:
    #    name_dict = name_query(entity_type, entity_id)
    #    if name_dict:
    #        name_maps.update(name_dict)
    #    else:
    #        to_process.append(entity_id)
    #        print(entity_id, "Failed ES lookup on index \
    #                '{}s'".format(entity_type.text))
    to_process = entity_ids

    # Use API search for the remainding papers
    name_maps.update(name_mag_multiquery(entity_type, to_process))

    return name_maps


if __name__ == '__main__':
    #author_name_mag_query(2100918400)
    print(affiliation_name_mag_multiquery([1334950195]))
