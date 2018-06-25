import os, sys, json, uuid, hashlib
from multiprocessing import Pool
from elasticsearch_dsl.connections import connections
from datetime import datetime
from graph.schema_cache import AuthorGroup, PaperGroup, AuthorInfo, PaperInfo

hostname = "130.56.248.105:9200"

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
    connections.create_connection(hosts = hostname, timeout=20)
    print("Elasticsearch connections initialized")

def saveNewAuthorCache(cache):
    print("starting cache")
    init_es()
    assert cache["Type"] in cache_types["author_group"]
    doc = AuthorGroup()
    doc.Type = cache["Type"]
    doc.NormalizedName = cache["NormalizedName"]
    doc.DisplayName = cache["DisplayName"]
    doc.Year = cache["Year"] if ("Year" in cache and cache['Year'].isdigit()) else None
    doc.Affiliations = cache["Affiliation"] if "Affiliation" in cache else None
    doc.Keywords = cache["Keywords"] if "Keywords" in cache else None
    doc.Url = cache['Url'] if 'Url' in cache else None
    doc.Citation = cache['Citation']
    doc.AuthorIds = cache['AuthorIds'] if 'AuthorIds' in cache else None
    doc.CreatedDate = datetime.now()
    doc.meta.id = generate_uuid("{}-{}".format(doc.Type, doc.NormalizedName))
    doc.save()
    print("finished caching")
