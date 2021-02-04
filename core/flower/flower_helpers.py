def is_self_cite(row, e_id_name, entity_name):
    return not set(entity_name).isdisjoint(set(row[e_id_name + '_citing'])) and not set(entity_name).isdisjoint(set(row[e_id_name + '_cited']))
