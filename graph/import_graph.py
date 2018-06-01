import os, sys, csv
from elasticsearch_dsl.connections import connections
from datetime import datetime
from schema import *

es_host = "130.56.248.105:9200"
filedir = "smallsamples"

def init_es():
	connections.create_connection(hosts = es_host, timeout=20)
	print("Elasticsearch connections initialized")

def import_Authors():
    file="Authors"
    print("Starting", file)
    filepath = os.path.join(filedir, "{}.txt".format(file))
    reader = csv.reader(open(filepath), delimiter="\t")
    for r in reader:
        doc = Authors()
        doc.meta.id = doc.AuthorId = int(r[0])
        doc.Rank = int(r[1])
        doc.NormalizedName = r[2]
        doc.DisplayName = r[3]
        doc.LastKnownAffiliationId = int(r[4]) if r[4] != "" else None
        doc.PaperCount = int(r[5]) if r[5] != "" else None
        doc.CitationCount = int(r[6]) if r[6] != "" else None
        doc.CreatedDate = datetime.strptime(r[7], "%Y-%m-%d")
        doc.save()
    print("Finished", file)

def import_Affiliations():
    file="Affiliations"
    print("Starting", file)
    filepath = os.path.join(filedir, "{}.txt".format(file))
    reader = csv.reader(open(filepath), delimiter="\t")
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
    print("Finished", file)

def import_Papers():
    file="Papers"
    print("Starting", file)
    filepath = os.path.join(filedir, "{}.txt".format(file))
    reader = csv.reader(open(filepath), delimiter="\t")
    for r in reader:
        doc = Papers()
        doc.meta.id = doc.PaperId = int(r[0])
        doc.Rank = int(r[1])
        doc.Doi = r[2]
        doc.DocType = r[3]
        doc.PaperTitle = r[4]
        doc.OriginalTitle = r[5]
        doc.BookTitle = r[6]
        doc.Year = int(r[7])
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
        doc.save()
    print("Finished", file)

def import_PaperAuthorAffiliations():
    file="PaperAuthorAffiliations"
    print("Starting", file)
    filepath = os.path.join(filedir, "{}.txt".format(file))
    reader = csv.reader(open(filepath), delimiter="\t")
    for r in reader:
        doc = PaperAuthorAffiliations()
        doc.meta.id = doc.PaperId = int(r[0])
        doc.AuthorId = int(r[1])
        doc.AffiliationId = int(r[2]) if r[2] != "" else None
        doc.AuthorSequenceNumber = int(r[3])
        doc.save()
    print("Finished", file)

def import_ConferenceInstances():
    file="ConferenceInstances"
    print("Starting", file)
    filepath = os.path.join(filedir, "{}.txt".format(file))
    reader = csv.reader(open(filepath), delimiter="\t")
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
    print("Finished", file)

def main(argv):
    init_es()
    import_Authors()
    import_Papers()
    import_Affiliations()

if __name__ == "__main__":
    main(sys.argv)
