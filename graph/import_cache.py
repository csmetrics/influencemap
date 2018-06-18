import os, sys, json, uuid, hashlib
from multiprocessing import Pool
from elasticsearch_dsl.connections import connections
from datetime import datetime
from config import conf
from schema_cache import AuthorGroup, PaperGroup, AuthorInfo, PaperInfo

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


# sample
def import_author_info():
    init_es()
    author = AuthorInfo()
    author.NormalizedName = "lexing xie"
    author.DisplayName = "Lexing Xie"
    author.AuthorIds = [2100918400, 2799110339]
    author.Papers = [{
            "AuthorId": 2100918400,
            "PaperIds": [111111, 222222, 333333]
        },{
            "AuthorId": 2799110339,
            "PaperIds": [444444, 555555, 666666]
        }]
    author.CreatedDate = datetime.now()
    author.meta.id = generate_uuid(author.NormalizedName)
    author.save()
    print("Cache added", author.NormalizedName)

# sample
def import_paper_info():
    init_es()
    paper = PaperInfo()
    paper.meta.id = paper.PaperId = 2771061228
    paper.Authors = [{
        "AuthorId": 111111,
        "AffiliationId": 100000
    },{
        "AuthorId": 222222,
        "AffiliationId": 100000
    }]
    paper.References = [{
        "PaperId": 2394483183,
        "Author": [{
            "AuthorId": 111111,
            "AffiliationId": 100000
        },{
            "AuthorId": 222222,
            "AffiliationId": 100000
        }],
        "ConferenceId": 232323
    },{
        "PaperId": 1294483183,
        "Author": [{
            "AuthorId": 333333,
            "AffiliationId": 400000
        },{
            "AuthorId": 222222,
            "AffiliationId": 100000
        }],
        "JournalId": 454545
    }]
    paper.Citations = [{
        "PaperId": 2394483183,
        "Author": [{
            "AuthorId": 111111,
            "AffiliationId": 100000
        },{
            "AuthorId": 222222,
            "AffiliationId": 100000
        }],
        "ConferenceId": 232323
    },{
        "PaperId": 1294483183,
        "Author": [{
            "AuthorId": 333333,
            "AffiliationId": 400000
        },{
            "AuthorId": 222222,
            "AffiliationId": 100000
        }],
        "JournalId": 454545
    }]
    paper.CreatedDate = datetime.now()
    paper.save()
    print("Cache added - paper", paper.PaperId)


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
    # main(sys.argv)
    # import_author_info()
    import_paper_info()
