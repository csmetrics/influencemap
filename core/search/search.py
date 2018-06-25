from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
import sys

def printDict(dictionary):
    for key in dictionary.keys():
        print(key)
        print("\n\n\n\n{}".format(dictionary[key]))

d = {
    'author': {
        "keys": ["AuthorId", "NormalizedName", "DisplayName", "PaperCount", "CitationCount"],
        "index": "authors"
    },
    'institution': {
        "keys": ["AffiliationId", "NormalizedName", "DisplayName", "PaperCount", "CitationCount", "OfficialPage", "WikiPage"],
        "index": "affiliations"
    },    
    'conference': {
        "keys": ["ConferenceSeriesId", "NormalizedName", "DisplayName", "PaperCount", "CitationCount"],
        "index": "conferenceseries"
    },    
    'journal': {
        "keys": ["JournalId", "NormalizedName", "DisplayName", "PaperCount", "CitationCount", "Issn", "Publisher", "Webpage"],
        "index": "journals"
    },
    'paper': {
        "keys": ['PaperId', 'PaperTitle', 'OriginalTitle', 'CitationCount', 'Year'],
        "index": 'papers'
    }   
}

def search_name(name, entity_type, page=1):
    keys = d[entity_type]['keys']
    idx = d[entity_type]['index']
    client = Elasticsearch()
    s = Search(using=client, index=idx)
    if entity_type == 'conference':
        s = s.query("match", DisplayName=name)
    elif entity_type=='paper':
        s = s.query("match", PaperTitle=name)
    else: 
        s = s.query("match", NormalizedName=name)
    s = s[0+((page-1)*15):15+((page-1)*15)]
    response = s.execute()

    result = list()
    for r in response:
        entity_dict = dict()
        for key in keys:
            entity_dict[key] = r[key]
        result.append(entity_dict)
        print(entity_dict)
    return result


if __name__ == "__main__":
    if len(sys.argv) == 2:
        search_author(sys.argv[1])
    elif len(sys.argv) == 3:
        search_author(sys.argv[1], abs(int(sys.argv[2])))

