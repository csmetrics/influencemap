import html
from core.search.query_info import query_entity_by_id, query_entities_by_list, convert_id


def get_names_from_entity(entity_ids, id_field, with_id=False):
    # print("get_names_from_entity", id_field, id_str, entity_ids)
    entities = query_entities_by_list(id_field, entity_ids)
    result = {convert_id(e['id'], id_field): html.escape(e['display_name'], quote=True)
              for e in entities}
    id_name_dict = {eid: result[eid] if eid in result else query_entity_by_id(id_field, eid)
                    for eid in entity_ids}
    if with_id:
        return id_name_dict
    return list(id_name_dict.values())


def get_names_from_conference_ids(entity_ids):
    return get_names_from_entity(entity_ids, "sources")


def get_names_from_affiliation_ids(entity_ids, with_id=False):
    return get_names_from_entity(entity_ids, "institutions", with_id=with_id)


def get_names_from_journal_ids(entity_ids):
    return get_names_from_entity(entity_ids, "sources")


def get_display_names_from_conference_ids(entity_ids):
    return get_names_from_entity(entity_ids, "sources", with_id=True)


def get_display_names_from_journal_ids(entity_ids):
    return get_names_from_entity(entity_ids, "sources", with_id=True)


def get_display_names_from_author_ids(entity_ids, with_id=False):
    return get_names_from_entity(entity_ids, "authors", with_id=with_id)


def get_display_names_from_fos_ids(entity_ids, with_id=False):
    return get_names_from_entity(entity_ids, "concepts", with_id=with_id)
