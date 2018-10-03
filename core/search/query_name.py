'''
Functions for querying database for entity names from entity ids.

date:   24.06.18
author: Alexander Soen
'''

from graph.config import conf
from core.utils.entity_type import Entity_type

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

def author_name_query(author_ids):
    ''' Find author name from id.
    '''
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Target
    authors_target = 'NormalizedName'

    # Query for paa
    authors_s = Search(index = 'authors', using = client)
    authors_s = authors_s.query('terms', AuthorId=author_ids)
    authors_s = authors_s.source([authors_target])
    authors_s = authors_s.params(request_timeout=30)

    names = list()
    for authors in authors_s.scan():
        # Add names to result
        names.append(authors[authors_target])
        
    return names


def author_name_dict_query(author_ids):
    ''' Find author name from id.
    '''
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Target
    authors_target = 'NormalizedName'

    # Query for paa
    authors_s = Search(index = 'authors', using = client)
    authors_s = authors_s.query('terms', AuthorId=author_ids)
    authors_s = authors_s.source([authors_target])
    authors_s = authors_s.params(request_timeout=30)

    names = dict()
    for authors in authors_s.scan():
        # Add names to result
        names[int(authors.meta.id)] = authors[authors_target]
        
    return names


def affiliation_name_query(affiliation_ids):
    ''' Find affiliation name from id.
    '''
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Target
    affi_target = 'NormalizedName'

    # Query for paa
    affi_s = Search(index = 'affiliations', using = client)
    affi_s = affi_s.query('terms', AffiliationId=affiliation_ids)
    affi_s = affi_s.source([affi_target])
    affi_s = affi_s.params(request_timeout=30)

    names = list()
    for affi in affi_s.scan():
        # Add names to result
        names.append(affi[affi_target])
        
    return names


def affiliation_name_dict_query(affiliation_ids):
    ''' Find affiliation name from id.
    '''
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Target
    affi_target = 'NormalizedName'

    # Query for paa
    affi_s = Search(index = 'affiliations', using = client)
    affi_s = affi_s.query('terms', AffiliationId=affiliation_ids)
    affi_s = affi_s.source([affi_target])
    affi_s = affi_s.params(request_timeout=30)

    names = dict()
    for affi in affi_s.scan():
        # Add names to result
        names[int(affi.meta.id)] = affi[affi_target]
        
    return names


def conference_name_query(conference_ids):
    ''' Find conference name from id.
    '''
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Target
    conf_target = 'NormalizedName'

    # Query for paa
    conf_s = Search(index = 'conferenceseries', using = client)
    conf_s = conf_s.query('terms', ConferenceSeriesId=conference_ids)
    conf_s = conf_s.source([conf_target])
    conf_s = conf_s.params(request_timeout=30)

    names = list()
    for conference in conf_s.scan():
        # Add names to result
        names.append(conference[conf_target])

    return names


def conference_name_dict_query(conference_ids):
    ''' Find conference name from id.
    '''
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Target
    conf_target = 'NormalizedName'

    # Query for paa
    conf_s = Search(index = 'conferenceseries', using = client)
    conf_s = conf_s.query('terms', ConferenceSeriesId=conference_ids)
    conf_s = conf_s.source([conf_target])
    conf_s = conf_s.params(request_timeout=30)

    names = dict()
    for conference in conf_s.scan():
        # Add names to result
        names[int(conference.meta.id)] = conference[conf_target]

    return names


def journal_name_query(journal_ids):
    ''' Find journal name from id.
    '''
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Target
    jour_target = 'NormalizedName'

    # Query for paa
    jour_s = Search(index = 'journals', using = client)
    jour_s = jour_s.query('terms', JournalId=journal_ids)
    jour_s = jour_s.source([jour_target])
    jour_s = jour_s.params(request_timeout=30)

    names = list()
    for jour in jour_s.scan():
        # Add names to result
        names.append(jour[jour_target])

    return names


def journal_name_dict_query(journal_ids):
    ''' Find journal name from id.
    '''
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Target
    jour_target = 'NormalizedName'

    # Query for paa
    jour_s = Search(index = 'journals', using = client)
    jour_s = jour_s.query('terms', JournalId=journal_ids)
    jour_s = jour_s.source([jour_target])
    jour_s = jour_s.params(request_timeout=30)

    names = dict()
    for jour in jour_s.scan():
        # Add names to result
        names[int(jour.meta.id)] = jour[jour_target]

    return names


def name_query(entity_type, entity_name):
    ''' Query entity id for name depending on type.
    '''
    # Call query functions depending on type given
    # Author
    if entity_type == Entity_type.AUTH:
        return author_name_query(entity_name)

    # Affiliation
    if entity_type == Entity_type.AFFI:
        return affiliation_name_query(entity_name)

    # Conference
    if entity_type == Entity_type.CONF:
        return conference_name_query(entity_name)

    # Journal
    if entity_type == Entity_type.JOUR:
        return journal_name_query(entity_name)

    # Otherwise
    return None


def normalized_to_display(entity_name, index):
    '''
    '''
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Query for paa
    query_s = Search(index=index, using=client)
    query_s = query_s.query('match', NormalizedName=entity_name)
    query_s = query_s.source(['DisplayName'])

    print()
    print(index)
    for query in query_s.scan():
        # Return display name
        print(query, index)
        return query['DisplayName']
        
    return None
