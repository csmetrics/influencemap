import os, sys, csv
from multiprocessing import Pool
from elasticsearch.helpers import bulk
from elasticsearch_dsl.connections import connections
from datetime import datetime
from config import conf
from schema import *


def init_es():
    connections.create_connection(hosts = conf.get("elasticsearch.hostname"), timeout=60)
    print("Elasticsearch connections initialized")


def import_Authors(r):
    doc = Authors()
    doc.meta.index = "Authors".lower()
    doc.meta.id = doc.AuthorId = int(r[0])
    doc.Rank = int(r[1])
    doc.NormalizedName = r[2]
    doc.DisplayName = r[3]
    doc.LastKnownAffiliationId = int(r[4]) if r[4] != "" else None
    doc.PaperCount = int(r[5]) if r[5] != "" else None
    doc.PaperFamilyCount = int(r[6]) if r[6] != "" else None # after ver 2021-02-15
    doc.CitationCount = int(r[7]) if r[7] != "" else None
    doc.CreatedDate = datetime.strptime(r[8], "%Y-%m-%d")
    return doc.to_dict(True)


def import_Affiliations(r):
    doc = Affiliations()
    doc.meta.index = "Affiliations".lower()
    doc.meta.id = doc.AffiliationId = int(r[0])
    doc.Rank = int(r[1])
    doc.NormalizedName = r[2]
    doc.DisplayName = r[3]
    doc.GridId = r[4]
    doc.OfficialPage = r[5]
    doc.WikiPage = r[6]
    doc.PaperCount = int(r[7]) if r[7] != "" else None
    doc.PaperFamilyCount = int(r[8]) if r[8] != "" else None # after ver 2021-02-15
    doc.CitationCount = int(r[9]) if r[9] != "" else None
    doc.IsoCode = r[10] # after ver 2021-02-15
    doc.Latitude = float(r[11]) if r[11] != "" else None # after ver 2019-11-08
    doc.Longitude = float(r[12]) if r[12] != "" else None # after ver 2019-11-08
    doc.CreatedDate = datetime.strptime(r[13], "%Y-%m-%d")
    return doc.to_dict(True)


def import_Papers(r):
    doc = Papers()
    doc.meta.index = "Papers".lower()
    doc.meta.id = doc.PaperId = int(r[0])
    doc.Rank = int(r[1])
    doc.Doi = r[2]
    doc.DocType = r[3]
    doc.PaperTitle = r[4]
    doc.OriginalTitle = r[5]
    doc.BookTitle = r[6]
    doc.Year = int(r[7]) if r[7] != "" else None
    doc.date = datetime.strptime(r[8], "%Y-%m-%d") if r[8] != "" else None
    doc.OnlineDate = datetime.strptime(r[9], "%Y-%m-%d") if r[9] != "" else None # new attribute ver.2021-02-15
    doc.Publisher = r[10]

    doc.JournalId = int(r[11]) if r[11] != "" else None
    doc.ConferenceSeriesId = int(r[12]) if r[12] != "" else None
    doc.ConferenceInstanceId = int(r[13]) if r[13] != "" else None
    doc.Volume = r[14]
    doc.Issue = r[15]
    doc.FirstPage = r[16]
    doc.LastPage = r[17]
    doc.ReferenceCount = int(r[18]) if r[18] != "" else None
    doc.CitationCount = int(r[19]) if r[19] != "" else None
    doc.EstimatedCitation = int(r[20]) if r[20] != "" else None

    doc.OriginalVenue = r[21] # new attribute ver.2019-01-01
    doc.FamilyId = r[22] # new attribute ver.2019-11-08
    doc.FamilyRank = int(r[23]) if r[23] != "" else None # new attribute ver.2021-02-15
    doc.CreatedDate = datetime.strptime(r[24], "%Y-%m-%d")

    doc.LanguageCode = None
    doc.FieldOfStudy = None
    doc.SourceType = None
    doc.SourceUrl = None
    return doc.to_dict(True)


def import_PaperReferences(r):
    doc = PaperReferences()
    doc.meta.index = "PaperReferences".lower()
    doc.PaperId = int(r[0])
    doc.PaperReferenceId = int(r[1])
    doc.meta.id = "{}_{}".format(doc.PaperId, doc.PaperReferenceId)
    return doc.to_dict(True)


def import_PaperAuthorAffiliations(r):
    doc = PaperAuthorAffiliations()
    doc.meta.index = "PaperAuthorAffiliations".lower()
    doc.PaperId = int(r[0])
    doc.AuthorId = int(r[1])
    doc.meta.id = "{}_{}".format(doc.PaperId, doc.AuthorId)
    doc.AffiliationId = int(r[2]) if r[2] != "" else None
    doc.AuthorSequenceNumber = int(r[3])
    doc.OriginalAuthor = r[4] # new attribute ver.2019-11-08
    doc.OriginalAffiliation = r[5] # new attribute ver.2019-01-01
    return doc.to_dict(True)


def import_ConferenceInstances(r):
    doc = ConferenceInstances()
    doc.meta.index = "ConferenceInstances".lower()
    doc.meta.id = doc.ConferenceInstanceId = int(r[0])
    # doc.Rank = int(r[1]) # removed attr ver.2019-01-01
    doc.NormalizedName = r[1]
    doc.DisplayName = r[2]
    doc.ConferenceSeriesId = int(r[3]) if r[3] != "" else None
    doc.Location = r[4]
    doc.OfficialUrl = r[5]
    doc.StartDate = datetime.strptime(r[6], "%Y-%m-%d") if r[6] != "" else None
    doc.EndDate = datetime.strptime(r[7], "%Y-%m-%d") if r[7] != "" else None
    doc.AbstractRegistrationDate = datetime.strptime(r[8], "%Y-%m-%d") if r[8] != "" else None
    doc.SubmissionDeadlineDate = datetime.strptime(r[9], "%Y-%m-%d") if r[9] != "" else None
    doc.NotificationDueDate = datetime.strptime(r[10], "%Y-%m-%d") if r[10] != "" else None
    doc.FinalVersionDueDate = datetime.strptime(r[11], "%Y-%m-%d") if r[11] != "" else None
    doc.PaperCount = int(r[12]) if r[12] != "" else None
    doc.PaperFamilyCount = int(r[13]) if r[13] != "" else None # after ver 2021-02-15
    doc.CitationCount = int(r[14]) if r[14] != "" else None
    doc.Latitude = float(r[15]) if r[15] != "" else None # after ver 2019-11-08
    doc.Longitude = float(r[16]) if r[16] != "" else None # after ver 2019-11-08
    doc.CreatedDate = datetime.strptime(r[17], "%Y-%m-%d")
    return doc.to_dict(True)


def import_ConferenceSeries(r):
    doc = ConferenceSeries()
    doc.meta.index = "ConferenceSeries".lower()
    doc.meta.id = doc.ConferenceSeriesId = int(r[0])
    doc.Rank = int(r[1])
    doc.NormalizedName = r[2]
    doc.DisplayName = r[3]
    doc.PaperCount = int(r[4]) if r[4] != "" else None
    doc.PaperFamilyCount = int(r[5]) if r[5] != "" else None # after ver 2021-02-15
    doc.CitationCount = int(r[6]) if r[6] != "" else None
    doc.CreatedDate = datetime.strptime(r[7], "%Y-%m-%d")
    return doc.to_dict(True)


def import_Journals(r):
    doc = Journals()
    doc.meta.index = "Journals".lower()
    doc.meta.id = doc.JournalId = int(r[0])
    doc.Rank = int(r[1])
    doc.NormalizedName = r[2]
    doc.DisplayName = r[3]
    doc.Issn = r[4]
    doc.Publisher = r[5]
    doc.Webpage = r[6]
    doc.PaperCount = int(r[7]) if r[7] != "" else None
    doc.PaperFamilyCount = int(r[8]) if r[8] != "" else None # after ver 2021-02-15
    doc.CitationCount = int(r[9]) if r[9] != "" else None
    doc.CreatedDate = datetime.strptime(r[10], "%Y-%m-%d")
    return doc.to_dict(True)


def import_FieldsOfStudy(r):
    doc = FieldsOfStudy()
    doc.meta.index = "FieldsOfStudy".lower()
    doc.meta.id = doc.FieldOfStudyId = int(r[0])
    doc.Rank = int(r[1])
    doc.NormalizedName = r[2]
    doc.DisplayName = r[3]
    doc.MainType = r[4]
    doc.Level = int(r[5]) if r[5] != "" else None
    doc.PaperCount = int(r[6]) if r[6] != "" else None
    doc.CitationCount = int(r[7]) if r[7] != "" else None
    doc.CreatedDate = datetime.strptime(r[8], "%Y-%m-%d")
    doc.save()


def import_FieldOfStudyChildren(r):
    doc = FieldOfStudyChildren()
    doc.meta.index = "FieldOfStudyChildren".lower()
    doc.FieldOfStudyId = int(r[0])
    doc.ChildFieldOfStudyId = int(r[1])
    doc.meta.id = "{}_{}".format(doc.FieldOfStudyId, doc.ChildFieldOfStudyId)
    return doc.to_dict(True)


def import_PaperFieldsOfStudy(r):
    doc = PaperFieldsOfStudy()
    doc.meta.index = "PaperFieldsOfStudy".lower()
    doc.PaperId = int(r[0])
    doc.FieldOfStudyId = int(r[1])
    doc.Similarity = float(r[2])
    doc.meta.id = "{}_{}".format(doc.PaperId, doc.FieldOfStudyId)
    return doc.to_dict(True)


options = {
    "Authors": import_Authors,
    "Affiliations": import_Affiliations,
    "Papers": import_Papers,
    "PaperReferences": import_PaperReferences,
    "PaperAuthorAffiliations": import_PaperAuthorAffiliations,
    "ConferenceInstances": import_ConferenceInstances,
    "ConferenceSeries": import_ConferenceSeries,
    "Journals": import_Journals,
    "FieldsOfStudy": import_FieldsOfStudy,
    "FieldOfStudyChildren": import_FieldOfStudyChildren,
    "PaperFieldsOfStudy": import_PaperFieldsOfStudy
}

def graph_import(v):
    data_type, filepath = v[0], v[1]
    print("Starting", filepath)
    init_es()
    myfile = (line.replace('\0','') for line in open(filepath))
    reader = csv.reader(myfile, delimiter="\t", quoting=csv.QUOTE_NONE)
    data = [options[data_type](r) for r in reader]
    bulk(connections.get_connection(), data)
    print("Finished", filepath)
    os.remove(filepath)


def main(argv):
    ### usage: e.g. `python import_graph 4 Papers`
    ### use csplit to split the huge file into small files.
    ### need raw files under filedir/Papers/

    filedir = os.path.join(conf.get("data.filedir"), conf.get("data.version"))
    numthreads = int(argv[1])
    data_type = argv[2]
    print("Importing", data_type)

    p = Pool(numthreads)
    if data_type in options:
        filepath = os.path.join(filedir, data_type)
        print("Reading files in dir", filepath)
        files = [os.path.join(filedir, data_type, f) for f in sorted(os.listdir(filepath))]
        print(files)
        p.map(graph_import, [(data_type, f) for f in files])

if __name__ == "__main__":
    main(sys.argv)
    #filename = os.path.join(conf.get("data.filedir"), conf.get("data.version"), "sorted_PaperFieldsOfStudy.txt")
    #update_Papers_FieldsOfStudy(filename)
