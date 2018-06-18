import os, sys, json, uuid, hashlib
from multiprocessing import Pool
from elasticsearch_dsl.connections import connections
from datetime import datetime
from config import conf
from schema_cache import AuthorGroup, PaperGroup

cache_types = {
    "author_group": [
        "anu_researchers",
        "fields_medalists",
        "turing_award_winners",
    ],
    "paper_group": [
        "publication_venue",
        "univ_field",
        "universities"
    ]
}

def generate_uuid(seed = None):
    return uuid.uuid1() if not seed else hashlib.sha1(str.encode(seed)).hexdigest()


def init_es():
    connections.create_connection(hosts = conf.get("elasticsearch.hostname"), timeout=20)
    print("Elasticsearch connections initialized")


def import_author_group_cache(filepath):
    print("Starting", filepath)
    init_es()
    cachefile = json.load(open(filepath))
    # print(cachefile)
    for cache in cachefile:
        assert cache["Type"] in cache_types["author_group"]
        doc = AuthorGroup()
        doc.Type = cache["Type"]
        doc.NormalizedName = cache["NormalizedName"]
        doc.DisplayName = cache["DisplayName"]
        doc.Year = cache["Year"] if "Year" in cache else None
        doc.Affiliations = cache["Affiliation"] if "Affiliation" in cache else None
        doc.Keywords = cache["Keywords"] if "Keywords" in cache else None
        doc.CreatedDate = datetime.now()
        doc.meta.id = generate_uuid("{}-{}".format(doc.Type, doc.NormalizedName))
        doc.save()
    print("Finished", filepath)

def import_paper_group_cache(filepath):
    print("Starting", filepath)
    init_es()
    cachefile = json.load(open(filepath))
    # print(cachefile)
    for cache in cachefile:
        assert cache["Type"] in cache_types["paper_group"]
        doc = PaperGroup()
        doc.Type = cache["Type"]
        doc.NormalizedName = cache["NormalizedName"]
        doc.DisplayName = cache["DisplayName"]
        doc.PaperIds = cache["PaperIds"]
        doc.Year = cache["Year"] if "Year" in cache else None
        doc.Field = cache["Field"] if "Field" in cache else None
        doc.Keywords = cache["Keywords"] if "Keywords" in cache else None
        doc.CreatedDate = datetime.now()
        doc.meta.id = generate_uuid("{}-{}={}".format(doc.Year, doc.Field, doc.NormalizedName))
        doc.save()
    print("Finished", filepath)


def main(argv):
    data_dir = "cache_sample"
    for data_file in os.listdir(data_dir):
        filepath = os.path.join(data_dir, data_file)
        print("Reading cache files", filepath)
        if "author" == data_file.split('_')[0]:
            import_author_group_cache(filepath)
        if "paper" == data_file.split('_')[0]:
            import_paper_group_cache(filepath)

if __name__ == "__main__":
    main(sys.argv)
