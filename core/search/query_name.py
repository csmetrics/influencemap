import core.search.query_name_db as qn_db
import core.search.query_name_mag as qn_mag

from core.utils.entity_type import Entity_type
from core.search.mag_interface import APIKeyError

def name_check_query(entity_type, entity_ids, mag_first=False):
    
    if mag_first:
        try:
            return qn_mag.name_mag_multiquery(entity_type, entity_ids).values()
        except APIKeyError:
            pass

    return qn_db.name_query(entity_type, entity_ids)

def name_check_dict_query(entity_type, entity_ids, mag_first=False):
    
    if mag_first:
        try:
            return qn_mag.name_mag_multiquery(entity_type, entity_ids)
        except APIKeyError:
            pass

    return qn_db.name_dict_query(entity_type, entity_ids)

def get_all_normalised_names(entity_dict, mag_first=False):

    normalised_names = []

    if "AuthorIds" in entity_dict and entity_dict["AuthorIds"]:
        normalised_names += name_check_query(
            Entity_type.AUTH, entity_dict['AuthorIds'], mag_first=mag_first)

    if "ConferenceIds" in entity_dict and entity_dict["ConferenceIds"]:
        normalised_names += name_check_query(
            Entity_type.CONF, entity_dict['ConferenceIds'], mag_first=mag_first)

    if "AffiliationIds" in entity_dict and entity_dict["AffiliationIds"]:
        normalised_names += name_check_query(
            Entity_type.AFFI, entity_dict['AffiliationIds'], mag_first=mag_first)

    if "JournalIds" in entity_dict and entity_dict["JournalIds"]:
        normalised_names += name_check_query(
            Entity_type.JOUR, entity_dict['JournalIds'], mag_first=mag_first)

    return normalised_names

def get_conf_journ_display_names(entity_dict, mag_first=False):

    display_dict = dict()

    if "ConferenceIds" in entity_dict and entity_dict["ConferenceIds"]:
        display_dict["Conference"] = name_check_query(
            Entity_type.CONF, entity_dict['ConferenceIds'], mag_first=mag_first)

    if "JournalIds" in entity_dict and entity_dict["JournalIds"]:
        display_dict["Journal"] = name_check_query(
            Entity_type.JOUR, entity_dict['JournalIds'], mag_first=mag_first)

    return display_dict