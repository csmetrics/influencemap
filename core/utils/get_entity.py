import pandas as pd
from core.search.mag_interface import *
import core.utils.entity_type as ent

entity_search_details = {
  "AUTH": {
    "expr": "AuN='{}'",
    "attributes": "Id,AuN",
  },
  "AFFI": {
    "expr": "AfN='{}'",
    "attributes": "Id,AfN",
  },
  "CONF": {
    "expr": "CN='{}'",
    "attributes": "Id,CN",
  },
}

def entity_from_name(name, e_type):
    MAS_URL_PREFIX = "https://api.labs.cognitive.microsoft.com"
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate?mode=json")
    search_details = entity_search_details[e_type.ident]
    query = {
      "expr": search_details['expr'].format(name),
      "count": 100,
      "attributes": search_details['attributes']
    }
    data = query_academic_search("get", url, query)

    name_tag = search_details['attributes'].split(',')[1]
    entity_list = list()
    for res_row in data['entities']:
        entity = ent.Entity(res_row[name_tag], str(res_row['Id']), e_type)
        entity_list.append(entity)

    return entity_list
