import os, sys, json, uuid, hashlib
from multiprocessing import Pool
from elasticsearch_dsl.connections import connections
from datetime import datetime
from graph.schema_cache import BrowseCache, AuthorGroup, PaperGroup, AuthorInfo, PaperInfo
from graph.config import conf

hostname = conf.get("elasticsearch.hostname")


def generate_uuid(seed = None):
    return uuid.uuid1() if not seed else hashlib.sha1(str.encode(seed)).hexdigest()


def init_es():
    connections.create_connection(hosts = hostname, timeout=20)
    print("Elasticsearch connections initialized")

def saveNewAuthorGroupCache(cache):
    print("starting cache")
    init_es()
    assert cache["Type"] in cache_types["author_group"]
    doc = AuthorGroup()
    doc.Type = cache["Type"]
    doc.NormalizedNames = cache["NormalizedNames"]
    doc.DisplayName = cache["DisplayName"]
    doc.Year = cache["Year"] if ("Year" in cache and cache['Year'].isdigit()) else None
    doc.Affiliations = cache["Affiliations"] if "Affiliations" in cache else None
    doc.Keywords = cache["Keywords"] if "Keywords" in cache else None
    doc.Url = cache['Url'] if 'Url' in cache else None
    doc.Citation = cache['Citation']
    doc.AuthorIds = cache['AuthorIds'] if 'AuthorIds' in cache else None
    doc.CreatedDate = datetime.now()
    doc.meta.id = generate_uuid("{}-{}".format(doc.Type, doc.DisplayName))
    doc.meta.index = "browse_author_group"
    doc.save()
    print("finished caching")

def saveNewPaperGroupCache(cache):
    print("starting cache")
    init_es()
    assert cache["Type"] in cache_types["paper_group"]
    doc = PaperGroup()
    doc.Type = cache["Type"]
    doc.NormalizedName = cache["NormalizedName"]
    doc.DisplayName = cache["DisplayName"]
    doc.PaperIds = cache["PaperIds"]
    doc.Year = cache["Year"] if ("Year" in cache and cache['Year'].isdigit()) else None
    doc.Field = cache["Field"] if "Field" in cache else None
    doc.Keywords = cache["Keywords"] if "Keywords" in cache else None
    doc.CreatedDate = datetime.now()
    doc.meta.id = generate_uuid("{}-{}={}".format(doc.Year, doc.Field, doc.NormalizedName))
    doc.meta.index = "browse_paper_group"
    doc.save()


def saveNewBrowseCache(cache):
    print("starting cache")

    init_es()

    # validation
    assert "DisplayName" in cache
    assert "EntityIds" in cache
    assert "Type" in cache

    doc = BrowseCache()

    # required fields
    doc.Type = cache["Type"]
    doc.DisplayName = cache["DisplayName"]
    doc.EntityIds = {}
    for key in cache["EntityIds"]:
        doc.EntityIds[key] = cache["EntityIds"][key]

    # optional fields
    if "Citation" in cache:                               doc.Citation = cache["Citation"]
    if "Year" in cache and str(cache["Year"]).isdigit() : doc.Year = cache["Year"]
    if "Field" in cache:                                  doc.Field = cache["Field"]
    if "Affiliations" in cache:                           doc.Affiliations = cache["Affiliations"]
    if "Url" in cache:                                    doc.Url = cache["Url"]
    if "PhotoUrl" in cache:                               doc.PhotoUrl = cache["PhotoUrl"]

    for key,value in cache.items():
        if key not in ["Type","DisplayName","EntityIds","Citation","Year","Field","Affiliations","Url","PhotoUrl"]: doc[key] = value

    # meta data
    doc.CreatedDate = datetime.now()
    doc.meta.id = generate_uuid("{}-{}".format(doc.DisplayName, doc.Type))
    doc.meta.index = "browse_cache"
    print(doc.to_dict())
    doc.save()

    # return generated id for document
    return doc.meta.id




import json
from core.search.query_info import paper_info_mag_check_multiquery

batchPath = "/home/u5798145/papers_to_cache"


def addToBatch(new_papers):
    with open(batchPath, 'r') as fh:
        papers = json.loads(fh.read())
    papers += new_papers
    papers = list(set(papers))
    with open(batchPath, 'w') as fh:
        json.dump(papers,fh)

def getBatch():
    with open(batchPath, 'r') as fh:
        papers = json.loads(fh.read())
    return papers

def emptyBatch():
    with open(batchPath, 'w') as fh:
        json.dump([],fh)

def cacheBatch():
    batchsize = 150
    while sizeBatch() > 0:
        batch = getBatch()
        batchindex = min([batchsize, len(batch)])
        minibatch = batch[0:batchindex]
        rebatch = batch[batchindex:len(batch)]
        print("caching {} papers".format(len(minibatch)))
        paper_info_mag_check_multiquery(minibatch)
        print("{} papers remaining in batch".format(len(rebatch)))
        emptyBatch()
        addToBatch(rebatch)

def sizeBatch():
    with open(batchPath, 'r') as fh:
        papers = json.loads(fh.read())
    return len(papers)

def main():
    if len(sys.argv) > 2:
        if sys.argv[1] == "batch":
            if sys.argv[2] == "get":
                for line in getBatch():
                    print(line)
            elif sys.argv[2] == "empty":
                emptyBatch()
            elif sys.argv[2] == "cache":
                cacheBatch()
            elif sys.argv[2] == "add" and len(sys.argv) > 3:
                addToBatch(sys.argv[3].split(','))
            elif sys.argv[2] == "size":
                print(sizeBatch())


if __name__ == '__main__':
    main()
