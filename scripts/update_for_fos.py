'''
Update cache to include fos information
'''
from datetime import datetime

from elasticsearch_dsl import Search, Q

from core.elastic import client
from core.search.cache_data import cache_paper_info
from core.search.query_info_db import paper_info_multiquery

# Constants
NUM_PAPERS = 1

# Elastic search client

THRESHOLD_DATE = datetime(2019, 3, 6, 10, 43, 45, 734484) 

# Memory for deleting entries which no longer exist
last_papers = set()

while True:
    # Specify the query
    paper_info_s = Search(index='paper_info', using=client)
    paper_info_s = paper_info_s.sort({ "CreatedDate": { "order": "desc" } })
    paper_info_s = paper_info_s.update_from_dict({ "query": { "bool": { "must_not": [ { "exists": { "field": "FieldsOfStudy" } } ], "must": { "range": { "CreatedDate": { "lt": THRESHOLD_DATE } } } } } })
    paper_info_s = paper_info_s.source(['PaperId'])

    # Get number of query results
    results = paper_info_s[:NUM_PAPERS]
    papers = [x.PaperId for x in results.execute()]

    # Check if the paper has been seen before, and thus needs to be deleted
    checked_papers = last_papers.intersection(set(papers))
    if checked_papers:
        delete_info_s = Search(index='paper_info', using=client)
        delete_info_s = delete_info_s.query("match", PaperId=list(checked_papers))
        delete_info_s.delete()
    last_papers = set(papers).difference(checked_papers)
    papers = list(last_papers)

    print(papers)

    # Get updated information
    process_res, partial_res = paper_info_multiquery(papers) #, force=True)

    # Generate cached entries
    cache_paper_info(process_res)
    cache_paper_info(partial_res, chunk_size=100)
