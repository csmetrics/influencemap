import json

entity_config = {
  'author': {
    'keys_to_make_dictionaries':[
      ['E']
    ],
    'key_change':[
      ['eid', 'Id'],
      ['normalisedName', 'AuN'],
      ['name', 'DAuN'],
      ['citations', 'CC'],
      ['affiliation', 'E', 'LKA', 'AfN'],
      ['affiliationId', 'E', 'LKA', 'AfId']
    ],
    'composite_aggregation': {},
    'id_key': 'authorId'
  },
  'conference': {
    'keys_to_make_dictionaries':[],
    'key_change':[
      ['eid', 'Id'],
      ['normalisedName', 'CN'],
      ['name', 'DCN'],
      ['citations', 'CC'],
      ['fieldOfStudy', 'FN'],
      ],
    'composite_aggregation': {
      'F': ['FN']
    },
    'id_key': 'conferenceSeriesId'
  },
  'journal': {
    'keys_to_make_dictionaries':[],
    'key_change':[
      ['eid', 'Id'],
      ['normalisedName', 'JN'],
      ['name', 'DJN'],
      ['citations', 'CC'],
    ],
    'composite_aggregation': {},
    'id_key': 'journalId'
  },
  'institution': {
    'keys_to_make_dictionaries':[
      ['E']
    ],
    'key_change':[
      ['eid', 'Id'],
      ['normalisedName', 'AfN'],
      ['name', 'DAfN'],
      ['citations', 'CC'],
      ['paperCount', 'E', 'PC'],
    ],
    'composite_aggregation': {},
    'id_key': 'affiliationId'
  },
  'paper': {
    'keys_to_make_dictionaries':[],
    'key_change':[
      ['eid', 'Id'],
      ['title', 'Ti'],
      ['languageCode', 'L'],
      ['year', 'Y'],
      ['date', 'D'],
      ['citations', 'CC'],
      ['estimatedCitations', "ECC"],
      ['authorName', 'AuN'],
      ['authorId', 'AuId'], 
      ['fieldOfStudy', 'FN'],
      ['conferenceSeriesName', 'CN'],
      ['conferenceSeriesId', 'CId'],
      ['journalName', 'JN'],
      ['journalId', 'JId'],
      ['affiliationName', 'AfN'],
      ['affiliationId', 'AfId']
    ],
    'composite_aggregation': {
        "AA": ["AuId", "AuN", "AfId", "AfN"],
        "F": ["FN"],
        "C": ["CN", "CId"],
        "J": ["JN", "JId"],
    }
  },
}


def get_nested_value(dictionary, keys, rtn_func=lambda x: x):
    if keys == []:
        return rtn_func(dictionary)
    else:
        return get_nested_value(dictionary[keys[0]], keys[1:], rtn_func)

def aggregate_composite_values(result, composite_aggregation):
    for table, attributes in composite_aggregation.items():
        for attr in attributes:
            try:
                result[attr] = [row[attr] for row in result[table]]
            except:
                result[attr] = None
    return result
                    
def turn_strings_to_dictionaries(result, keys_to_make_dictionaries):
    for keys in keys_to_make_dictionaries:
        try:
            result[keys[-1]] = get_nested_value(result, keys, json.loads)
        except:
            result[keys[-1]] = None
    return result

def result_to_dictionary(result, key_change):
    formatted_dictionary = dict()
    for elem in key_change:
        try:
            formatted_dictionary[elem[0]] = get_nested_value(result, elem[1:])
        except:
            formatted_dictionary[elem[0]] = None
    return formatted_dictionary

def link_papers_to_entities(paper_list, entity_list, entityType):
    entities = dict()
    for entity in entity_list:
        entity['papers'] = list()
        entity['paperCount'] = 0
        entities[entity['eid']] = entity
    if len(entity_list) == 1:
        entities[entity_list[0]['eid']]['papers'] = paper_list
        entities[entity_list[0]['eid']]['paperCount'] = len(paper_list)
    else:
        excluded_papers = 0
        for paper in paper_list:
            try:
                for eid in paper[entity_config[entityType]['id_key']]:
                    if eid in entities.keys():
                        entities[eid]['papers'].append(paper)
                        entities[eid]['paperCount'] += 1
            except:
                excluded_papers += 1
        if excluded_papers > 0:
            print("Some papers were excluded due to an absence of ids, "+str(excluded_papers)+" were excluded.")
            print(str(len(paper_list)-excluded_papers)+" where included.")
    return entities

def or_query_builder(base_query, inputs):
    if len(inputs) > 1:
        out = "Or({})"
        sub_constraints = [base_query.format(input) for input in inputs]
        out = out.format(", ".join(sub_constraints))
    elif len(inputs) == 1:
        out= base_query.format(inputs[0])
    else:
        out = ""
    return out

def or_query_builder_list(base_query, ids):
    ''' or_query_builder, but returns a list of expressions to prevent url
        being too long.
    '''
    query_list = list()
    inputs = list() + ids
    while inputs:
        if len(inputs) > 1:
            out = "Or({})"
            sub_constraints = list()
            # Incrementally add constraints
            while len(', '.join(sub_constraints)) + len(out) < 1000 and inputs:
                sub_constraints.append(base_query.format(inputs.pop(0)))
                
            out = out.format(", ".join(sub_constraints))
        elif len(inputs) == 1:
            out = base_query.format(inputs.pop(0))
        else:
            out = ""

        # Add current string
        query_list.append(out)

    return query_list
    
    

def parse_search_results(results, entityType):
    key_change = entity_config[entityType]['key_change']
    keys_to_make_dictionaries = entity_config[entityType]['keys_to_make_dictionaries']
    composite_aggregation = entity_config[entityType]['composite_aggregation']

    cleaning_func_1 = lambda x: aggregate_composite_values(x, composite_aggregation)
    cleaning_func_2 = lambda x: turn_strings_to_dictionaries(cleaning_func_1(x), keys_to_make_dictionaries)
    cleaning_func_combined = lambda x: result_to_dictionary(cleaning_func_2(x), key_change)

    data = [cleaning_func_combined(entity) for entity in results["entities"]]

    return data

def parse_search_resrow(row, entityType):
    key_change = entity_config[entityType]['key_change']
    keys_to_make_dictionaries = entity_config[entityType]['keys_to_make_dictionaries']
    composite_aggregation = entity_config[entityType]['composite_aggregation']

    cleaning_func_1 = lambda x: aggregate_composite_values(x, composite_aggregation)
    cleaning_func_2 = lambda x: turn_strings_to_dictionaries(cleaning_func_1(x), keys_to_make_dictionaries)
    cleaning_func_combined = lambda x: result_to_dictionary(cleaning_func_2(x), key_change)

    return cleaning_func_combined(row)
