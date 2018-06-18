import os, sys, json, uuid, hashlib
from multiprocessing import Pool
from elasticsearch_dsl.connections import connections
from datetime import datetime
from config import conf
from schema import BrowseCache

cache_types = [
    "anu_researchers",
    "fields_medalists",
    "turing_award_winners",
    "conferences"
]

def generate_uuid(seed = None):
    return uuid.uuid1() if not seed else hashlib.sha1(str.encode(seed)).hexdigest()


def init_es():
    connections.create_connection(hosts = conf.get("elasticsearch.hostname"), timeout=20)
    print("Elasticsearch connections initialized")


def import_json_cache(filepath):
    print("Starting", filepath)
    init_es()
    cachefile = json.load(open(filepath))
    # print(cachefile)
    for cache in cachefile:
        assert cache["Type"] in cache_types
        doc = BrowseCache()
        doc.Type = cache["Type"]
        doc.NormalizedName = cache["NormalizedName"]
        doc.DisplayName = cache["DisplayName"]
        doc.Year = cache["Year"] if "Year" in cache else None
        doc.AuthorIds = cache["AuthorIds"]
        doc.Papers = cache["Papers"]
        doc.Affiliations = cache["Affiliation"] if "Affiliation" in cache else None
        doc.Keywords = cache["Keywords"] if "Keywords" in cache else None
        doc.Citation = cache["Citation"] if "Citation" in cache else None
        doc.CreatedDate = datetime.now()
        doc.meta.id = generate_uuid(doc.NormalizedName)
        doc.save()
    print("Finished", filepath)


def main(argv):
    data_file = "cache_sample/anu.json"

    print("Reading cache files in dir", data_file)
    import_json_cache(data_file)

if __name__ == "__main__":
    main(sys.argv)
