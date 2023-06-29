import re
from graph.config import conf

def get_names_from_entity(entity_ids, index, id_field, name_field, with_id=False):
    id_name_dict = {eid: str(eid) for eid in entity_ids}
    if with_id:
        return id_name_dict
    ids = [id_name_dict[eid] for eid in entity_ids]
    return ids


def get_names_from_conference_ids(entity_ids):
    return get_names_from_entity(entity_ids, conf.get('index.conf_s'), "ConferenceSeriesId", "NormalizedName")

def get_names_from_affiliation_ids(entity_ids, with_id=False):
    return get_names_from_entity(entity_ids, conf.get('index.aff'), "AffiliationId", "DisplayName", with_id=with_id)

def get_names_from_journal_ids(entity_ids):
    return get_names_from_entity(entity_ids, conf.get('index.journal'), "JournalId", "NormalizedName")

def get_display_names_from_conference_ids(entity_ids):
    return get_names_from_entity(entity_ids, conf.get('index.conf_s'), "ConferenceSeriesId", "DisplayName", with_id=True)

def get_display_names_from_journal_ids(entity_ids):
    return get_names_from_entity(entity_ids, conf.get('index.journal'), "JournalId", "DisplayName", with_id=True)

def get_display_names_from_author_ids(entity_ids, with_id=False):
    return get_names_from_entity(entity_ids, conf.get('index.author'), "AuthorId", "DisplayName", with_id=with_id)

def get_display_names_from_fos_ids(entity_ids, with_id=False):
    return get_names_from_entity(entity_ids, conf.get('index.fos'), "FieldOfStudyId", "DisplayName", with_id=with_id)

