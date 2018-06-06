import os, sys, csv
from multiprocessing import Pool
from elasticsearch_dsl.connections import connections
from datetime import datetime
from schema import *

es_host = "130.56.248.105:9200"
filedir = "/localdata/MAG2018/data/graph/2018-04-13"

def init_es():
    connections.create_connection(hosts = es_host, timeout=20)
    print("Elasticsearch connections initialized")


def import_Authors(filepath):
    print("Starting", filepath)
    init_es()
    reader = csv.reader(open(filepath), delimiter="\t", quoting=csv.QUOTE_NONE)
    for r in reader:
        try:
            doc = Authors()
            doc.meta.id = doc.AuthorId = int(r[0])
            doc.Rank = int(r[1])
            doc.NormalizedName = r[2]
            doc.DisplayName = r[3]
            doc.LastKnownAffiliationId = int(r[4]) if r[4] != "" else None
            doc.PaperCount = int(r[5]) if r[5] != "" else None
            doc.CitationCount = int(r[6]) if r[6] != "" else None
            doc.CreatedDate = datetime.strptime(r[7], "%Y-%m-%d")
            doc.save(op_type="create")
        except Exception as e:
            print("[Error]", e)
     print("Finished", filepath)


def import_Affiliations(filepath):
    print("Starting", filepath)
    init_es()
    reader = csv.reader(open(filepath), delimiter="\t", quoting=csv.QUOTE_NONE)
    for r in reader:
        doc = Affiliations()
        doc.meta.id = doc.AffiliationId = int(r[0])
        doc.Rank = int(r[1])
        doc.NormalizedName = r[2]
        doc.DisplayName = r[3]
        doc.GridId = r[4]
        doc.OfficialPage = r[5]
        doc.WikiPage = r[6]
        doc.PaperCount = int(r[7]) if r[7] != "" else None
        doc.CitationCount = int(r[8]) if r[8] != "" else None
        doc.CreatedDate = datetime.strptime(r[9], "%Y-%m-%d")
        doc.save()
    print("Finished", filepath)


def import_Papers(filepath):
    print("Starting", filepath)
    init_es()
    reader = csv.reader(open(filepath), delimiter="\t", quoting=csv.QUOTE_NONE)
    for r in reader:
        try:
            doc = Papers()
            doc.meta.id = doc.PaperId = int(r[0])
            doc.Rank = int(r[1])
            doc.Doi = r[2]
            doc.DocType = r[3]
            doc.PaperTitle = r[4]
            doc.OriginalTitle = r[5]
            doc.BookTitle = r[6]
            doc.Year = int(r[7]) if r[7] != "" else None
            doc.date = datetime.strptime(r[8], "%Y-%m-%d") if r[8] != "" else None
            doc.Publisher = r[9]

            doc.JournalId = int(r[10]) if r[10] != "" else None
            doc.ConferenceSeriesId = int(r[11]) if r[11] != "" else None
            doc.ConferenceInstanceId = int(r[12]) if r[12] != "" else None
            doc.Volume = r[13]
            doc.Issue = r[14]
            doc.FirstPage = r[15]
            doc.LastPage = r[16]
            doc.ReferenceCount = int(r[17]) if r[17] != "" else None
            doc.CitationCount = int(r[18]) if r[18] != "" else None
            doc.EstimatedCitation = int(r[19]) if r[19] != "" else None
            doc.CreatedDate = datetime.strptime(r[20], "%Y-%m-%d")

            doc.LanguageCode = None
            doc.FieldOfStudyId = None
            doc.Similarity = None
            doc.SourceType = None
            doc.SourceUrl = None
            doc.save()
        except Exception as e:
            print("[Error]", e)
            print("in Paper:", r)
    print("Finished", filepath)


def import_PaperReferences(filepath):
    print("Starting", filepath)
    init_es()
    reader = csv.reader(open(filepath), delimiter="\t", quoting=csv.QUOTE_NONE)
    for r in reader:
        try:
            doc = PaperReferences()
            doc.PaperId = int(r[0])
            doc.PaperReferenceId = int(r[1])
            doc.meta.id = "{}_{}".format(doc.PaperId, doc.PaperReferenceId)
            doc.save(op_type="create")
        except Exception as e:
            print("[Error]", e)
    print("Finished", filepath)


def import_PaperAuthorAffiliations(filepath):
    print("Starting", filepath)
    init_es()
    reader = csv.reader(open(filepath), delimiter="\t", quoting=csv.QUOTE_NONE)
    for r in reader:
        try:
            doc = PaperAuthorAffiliations()
            doc.PaperId = int(r[0])
            doc.AuthorId = int(r[1])
            doc.meta.id = "{}_{}".format(doc.PaperId, doc.AuthorId)
            doc.AffiliationId = int(r[2]) if r[2] != "" else None
            doc.AuthorSequenceNumber = int(r[3])
            doc.save(op_type="create")
        except Exception as e:
            print("[Error]", e)
    print("Finished", filepath)


def import_ConferenceInstances(filepath):
    print("Starting", filepath)
    init_es()
    reader = csv.reader(open(filepath), delimiter="\t", quoting=csv.QUOTE_NONE)
    for r in reader:
        doc = ConferenceInstances()
        doc.meta.id = doc.ConferenceInstanceId = int(r[0])
        doc.Rank = int(r[1])
        doc.NormalizedName = r[2]
        doc.DisplayName = r[3]
        doc.ConferenceSeriesId = int(r[4]) if r[4] != "" else None
        doc.Location = r[5]
        doc.OfficialUrl = r[6]
        doc.StartDate = datetime.strptime(r[7], "%Y-%m-%d") if r[7] != "" else None
        doc.EndDate = datetime.strptime(r[8], "%Y-%m-%d") if r[8] != "" else None
        doc.AbstractRegistrationDate = datetime.strptime(r[9], "%Y-%m-%d") if r[9] != "" else None
        doc.SubmissionDeadlineDate = datetime.strptime(r[10], "%Y-%m-%d") if r[10] != "" else None
        doc.NotificationDueDate = datetime.strptime(r[11], "%Y-%m-%d") if r[11] != "" else None
        doc.FinalVersionDueDate = datetime.strptime(r[12], "%Y-%m-%d") if r[12] != "" else None
        doc.PaperCount = int(r[13]) if r[13] != "" else None
        doc.CitationCount = int(r[14]) if r[14] != "" else None
        doc.CreatedDate = datetime.strptime(r[15], "%Y-%m-%d")
        doc.save()
    print("Finished", filepath)


def import_ConferenceSeries(filepath):
    print("Starting", filepath)
    init_es()
    reader = csv.reader(open(filepath), delimiter="\t", quoting=csv.QUOTE_NONE)
    for r in reader:
        doc = ConferenceSeries()
        doc.meta.id = doc.ConferenceSeriesId = int(r[0])
        doc.Rank = int(r[1])
        doc.NormalizedName = r[2]
        doc.DisplayName = r[3]
        doc.PaperCount = int(r[4]) if r[4] != "" else None
        doc.CitationCount = int(r[5]) if r[5] != "" else None
        doc.CreatedDate = datetime.strptime(r[6], "%Y-%m-%d")
        doc.save()
    print("Finished", filepath)


def import_Journals(filepath):
    print("Starting", filepath)
    init_es()
    reader = csv.reader(open(filepath), delimiter="\t", quoting=csv.QUOTE_NONE)
    for r in reader:
        doc = Journals()
        doc.meta.id = doc.JournalId = int(r[0])
        doc.Rank = int(r[1])
        doc.NormalizedName = r[2]
        doc.DisplayName = r[3]
        doc.Issn = r[4]
        doc.Publisher = r[5]
        doc.Webpage = r[6]
        doc.PaperCount = int(r[7]) if r[7] != "" else None
        doc.CitationCount = int(r[8]) if r[8] != "" else None
        doc.CreatedDate = datetime.strptime(r[9], "%Y-%m-%d")
        doc.save()
    print("Finished", filepath)


def import_FieldsOfStudy(filepath):
    print("Starting", filepath)
    init_es()
    reader = csv.reader(open(filepath), delimiter="\t", quoting=csv.QUOTE_NONE)
    for r in reader:
        doc = FieldsOfStudy()
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
    print("Finished", filepath)


def import_FieldOfStudyChildren(filepath):
    print("Starting", filepath)
    init_es()
    reader = csv.reader(open(filepath), delimiter="\t")
    for r in reader:
        doc = FieldOfStudyChildren()
        doc.FieldOfStudyId = int(r[0])
        doc.ChildFieldOfStudyId = int(r[1])
        doc.meta.id = "{}_{}".format(doc.FieldOfStudyId, doc.ChildFieldOfStudyId)
        doc.save()
    print("Finished", filepath)


def main(argv):
    data_file = argv[1]
    print(data_file)
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
        "FieldOfStudyChildren": import_FieldOfStudyChildren
    }

    p = Pool(4)
    if data_file in options:
        filepath = os.path.join(filedir, data_file)
        print("Reading files in dir", )
        files = [os.path.join(filedir, data_file, f) for f in os.listdir(filepath)]
        print(files)
        p.map(options[data_file], files)

if __name__ == "__main__":
    main(sys.argv)
