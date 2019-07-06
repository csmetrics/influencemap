import core.search.query_paper_db as qp_db
import core.search.query_paper_mag as qp_mag

from core.utils.entity_type import Entity_type
from core.search.mag_interface import APIKeyError

def paper_check_query(entity_type, entity_ids, mag_first=False):
    
    if mag_first:
        try:
            return qp_mag.paper_mag_multiquery(entity_type, entity_ids)
        except APIKeyError:
            pass

    return qp_db.paper_query(entity_type, entity_ids)

def get_all_paper_ids(entity_dict, mag_first=False):

    paper_ids = entity_dict['PaperIds'] if "PaperIds" in entity_dict else []

    if "AuthorIds" in entity_dict and entity_dict["AuthorIds"]:
        paper_ids += paper_check_query(
            Entity_type.AUTH, entity_dict['AuthorIds'], mag_first=mag_first)

    if "ConferenceIds" in entity_dict and entity_dict["ConferenceIds"]:
        paper_ids += paper_check_query(
            Entity_type.CONF, entity_dict['ConferenceIds'], mag_first=mag_first)

    if "AffiliationIds" in entity_dict and entity_dict["AffiliationIds"]:
        paper_ids += paper_check_query(
            Entity_type.AFFI, entity_dict['AffiliationIds'], mag_first=mag_first)

    if "JournalIds" in entity_dict and entity_dict["JournalIds"]:
        paper_ids += paper_check_query(
            Entity_type.JOUR, entity_dict['JournalIds'], mag_first=mag_first)

    return paper_ids

if __name__ == "__main__":
    from core.utils.entity_type import Entity_type
    from core.search.academic_search import get_papers_from_entity_ids

    test1 = qp_mag.paper_mag_multiquery(Entity_type.AUTH, [2100918400])
    test2 = qp_db.paper_query(Entity_type.AUTH, [2100918400])