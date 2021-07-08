from operator import itemgetter

from core.search.elastic import client
from core.utils.entity_type import Entity_type

from elasticsearch_dsl import Search

def author_name_query(author_ids):
    if not author_ids:
        return []

    # Target
    authors_target = 'NormalizedName'

    # Query for paa
    authors_s = Search(index = 'authors', using = client)
    authors_s = authors_s.query('terms', AuthorId=author_ids)
    authors_s = authors_s.source([authors_target])
    authors_s = authors_s.params(request_timeout=30)

    return list(map(itemgetter(authors_target), authors_s.scan()))


def author_name_dict_query(author_ids):
    ''' Find author name from id.
    '''
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


def fos_name_level_dict_query(fos_ids):
    ''' Find field of study name from id.
    '''
    # Target
    fos_target = ['NormalizedName', 'Level']

    # Query for paa
    fos_s = Search(index = 'fieldsofstudy', using = client)
    fos_s = fos_s.query('terms', FieldOfStudyId=fos_ids)
    fos_s = fos_s.source(fos_target)
    fos_s = fos_s.params(request_timeout=30)

    names = dict()
    levels = dict()
    for fos in fos_s.scan():
        # Add names to result
        names[int(fos.meta.id)] = fos[fos_target[0]]
        levels[int(fos.meta.id)] = fos[fos_target[1]]

    return names, levels


def fos_name_query(fos_ids):
    if not fos_ids:
        return []
    
    fos_target = 'NormalizedName'

    # Query for paa
    fos_s = Search(index='fieldsofstudy', using=client)
    fos_s = fos_s.query('terms', FieldOfStudyId=fos_ids)
    fos_s = fos_s.source(fos_target)
    fos_s = fos_s.params(request_timeout=30)

    return list(map(itemgetter(fos_target), fos_s.scan()))


def affiliation_name_query(affiliation_ids):
    if not affiliation_ids:
        return []

    # Target
    affi_target = 'NormalizedName'

    # Query for paa
    affi_s = Search(index = 'affiliations', using = client)
    affi_s = affi_s.query('terms', AffiliationId=affiliation_ids)
    affi_s = affi_s.source([affi_target])
    affi_s = affi_s.params(request_timeout=30)

    return list(map(itemgetter(affi_target), affi_s.scan()))


def affiliation_name_dict_query(affiliation_ids):
    ''' Find affiliation name from id.
    '''
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
    if not conference_ids:
        return []

    # Target
    conf_target = 'NormalizedName'

    # Query for paa
    conf_s = Search(index = 'conferenceseries', using = client)
    conf_s = conf_s.query('terms', ConferenceSeriesId=conference_ids)
    conf_s = conf_s.source([conf_target])
    conf_s = conf_s.params(request_timeout=30)

    return list(map(str.lower, map(itemgetter(conf_target), conf_s.scan())))


def conference_name_dict_query(conference_ids):
    ''' Find conference name from id.
    '''
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
        names[int(conference.meta.id)] = conference[conf_target].lower()

    return names


def journal_name_query(journal_ids):
    if not journal_ids:
        return []

    # Target
    jour_target = 'NormalizedName'

    # Query for paa
    jour_s = Search(index = 'journals', using = client)
    jour_s = jour_s.query('terms', JournalId=journal_ids)
    jour_s = jour_s.source([jour_target])
    jour_s = jour_s.params(request_timeout=30)

    return list(map(itemgetter(jour_target), jour_s.scan()))


def journal_name_dict_query(journal_ids):
    ''' Find journal name from id.
    '''
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


def paper_name_query(paper_ids):
    if not paper_ids:
        return []
    target = 'PaperTitle'
    paper_s = Search(index='papers', using=client) \
                  .query('terms', PaperId=paper_ids) \
                  .source([target]) \
                  .params(request_timeout=30)
    return list(map(itemgetter(target), paper_s.scan()))


def get_conf_journ_display_names(entity_dict):

    display_dict = dict()

    if "ConferenceIds" in entity_dict and entity_dict["ConferenceIds"]:
        display_dict["Conference"] = name_check_query(
            Entity_type.CONF, entity_dict['ConferenceIds'])

    if "JournalIds" in entity_dict and entity_dict["JournalIds"]:
        display_dict["Journal"] = name_check_query(
            Entity_type.JOUR, entity_dict['JournalIds'])

    return display_dict
