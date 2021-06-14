import core.search.query_paper_db as qp_db

from core.utils.entity_type import Entity_type

def paper_check_query(entity_type, entity_ids):
    return qp_db.paper_query(entity_type, entity_ids)

def get_all_paper_ids(entity_dict):

    paper_ids = entity_dict['PaperIds'] if "PaperIds" in entity_dict else []

    if "AuthorIds" in entity_dict and entity_dict["AuthorIds"]:
        paper_ids += paper_check_query(
            Entity_type.AUTH, entity_dict['AuthorIds'])

    if "ConferenceIds" in entity_dict and entity_dict["ConferenceIds"]:
        paper_ids += paper_check_query(
            Entity_type.CONF, entity_dict['ConferenceIds'])

    if "AffiliationIds" in entity_dict and entity_dict["AffiliationIds"]:
        paper_ids += paper_check_query(
            Entity_type.AFFI, entity_dict['AffiliationIds'])

    if "JournalIds" in entity_dict and entity_dict["JournalIds"]:
        paper_ids += paper_check_query(
            Entity_type.JOUR, entity_dict['JournalIds'])

    return paper_ids

if __name__ == "__main__":
    from core.utils.entity_type import Entity_type
    from core.search.academic_search import get_papers_from_entity_ids

    test2 = qp_db.paper_query(Entity_type.AUTH, [2100918400])
