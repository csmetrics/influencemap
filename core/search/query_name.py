'''
Functions for querying database for entity names from entity ids.

date:   24.06.18
author: Alexander Soen
'''

from graph.config import conf
from core.utils.entity_type import Entity_type

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

def author_name_query(author_id):
    ''' Find author name from id.
    '''
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Target
    authors_target = 'NormalizedName'

    # Query result
    auth_name_res = dict()

    # Query for paa
    authors_s = Search(index = 'authors', using = client)
    authors_s = authors_s.query('match', AuthorId = author_id)
    authors_s = authors_s.source([authors_target])

    for authors in authors_s.scan():
        # Set name
        auth_name_res[author_id] = authors[authors_target]
        
        # Should only be one result
        break

    return auth_name_res


def affiliation_name_query(affiliation_id):
    ''' Find affiliation name from id.
    '''
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Target
    affi_target = 'NormalizedName'

    # Query result
    affi_name_res = dict()

    # Query for paa
    affi_s = Search(index = 'affiliations', using = client)
    affi_s = affi_s.query('match', AffiliationId = affiliation_id)
    affi_s = affi_s.source([affi_target])

    for affi in affi_s.scan():
        # Set name
        affi_name_res[affiliation_id] = affi[affi_target]
        
        # Should only be one result
        break

    return affi_name_res


def conference_name_query(conference_id):
    ''' Find conference name from id.
    '''
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Target
    conf_target = 'NormalizedName'

    # Query result
    conf_name_res = dict()

    # Query for paa
    conf_s = Search(index = 'conferenceinstances', using = client)
    conf_s = conf_s.query('match', ConferenceInstanceId = conference_id)
    conf_s = conf_s.source([conf_target])

    for conference in conf_s.scan():
        # Set name
        #conf_name_res[conference_id] = conference[conf_target]
        # quick fix for conference name
        conf_name_res[conference_id] = ' '.join(conference[conf_target].split()[:-1])
        
        # Should only be one result
        break

    if conf_name_res:
        return conf_name_res

    # Query for paa
    conf_s = Search(index = 'conferenceseries', using = client)
    conf_s = conf_s.query('match', ConferenceSeriesId = conference_id)
    conf_s = conf_s.source([conf_target])

    for conference in conf_s.scan():
        # Set name
        #conf_name_res[conference_id] = conference[conf_target]
        # quick fix for conference name
        conf_name_res[conference_id] = ' '.join(conference[conf_target].split()[:-1])
        
        # Should only be one result
        break

    return conf_name_res


def journal_name_query(journal_id):
    ''' Find journal name from id.
    '''
    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Target
    jour_target = 'NormalizedName'

    # Query result
    jour_name_res = dict()

    # Query for paa
    jour_s = Search(index = 'journals', using = client)
    jour_s = jour_s.query('match', JournalId = journal_id)
    jour_s = jour_s.source([jour_target])

    for jour in jour_s.scan():
        # Set name
        jour_name_res[journal_id] = jour[jour_target]
        
        # Should only be one result
        break

    return jour_name_res


def name_query(entity_type, entity_id):
    ''' Query entity id for name depending on type.
    '''
    # Call query functions depending on type given
    # Author
    if entity_type == Entity_type.AUTH:
        return author_name_query(entity_id)

    # Affiliation
    if entity_type == Entity_type.AFFI:
        return affiliation_name_query(entity_id)

    # Conference
    if entity_type == Entity_type.CONF:
        return conference_name_query(entity_id)

    # Journal
    if entity_type == Entity_type.JOUR:
        return journal_name_query(entity_id)

    # Otherwise
    return None
