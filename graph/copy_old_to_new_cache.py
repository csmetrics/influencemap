from multiprocessing import Pool
from elasticsearch_dsl import Search

from core.elastic import client
from graph.save_cache import saveNewBrowseCache

def get_documents(index):
    result = []
    q = {
      "query": {
        "match_all": {}
      }}

    s = Search(using=client, index=index)
    s.update_from_dict(q)
    for hit in s.scan():
        result.append(hit.to_dict())
    return result

def refile_author_groups():
    print("starting to refile author groups")
    documents = get_documents("browse_author_group")
    for i in range(len(documents)):
        document = documents[i]
        document["EntityIds"] = {"PaperIds":[],"AuthorIds": document["AuthorIds"] ,"AffiliationIds":[],"ConferenceIds":[],"JournalIds":[]}
        document = {k: v for k,v in document.items() if not (v==None or v==[] or v==[''] or v=="")}
        if document["Type"] == "anu_researcher": document["Type"] = "anu_researchers"
        print(document["Type"])
        saveNewBrowseCache(document)
    print("saved {} documents".format(len(documents)))

def refile_paper_groups():
    print("starting to refile paper groups")
    documents = get_documents("browse_paper_group")
    for i in range(len(documents)):
        document = documents[i]
        document["EntityIds"] = {"PaperIds":document["PaperIds"],"AuthorIds":[],"AffiliationIds":[],"ConferenceIds":[],"JournalIds":[]}
        document = {k: v for k,v in document.items() if not (v==None or v==[] or v==[''] or v=="")}
        saveNewBrowseCache(document)
    print("saved {} documents".format(len(documents)))

def main():
    refile_author_groups()
#    refile_paper_groups()

if __name__=="__main__":
    main()
