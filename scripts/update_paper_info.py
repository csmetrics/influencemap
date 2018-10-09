'''
'''

import os
import argparse
import threading
#from multiprocessing import Pool
from multiprocess import Pool
from datetime import datetime

from graph.config import conf
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q

#from core.search.query_info import paper_info_db_check_multiquery
from core.search.query_info_db    import paper_info_multiquery
from core.search.cache_data       import cache_paper_info

NUM_PAPERS = 20
THREADS = 4
PER_THREAD = NUM_PAPERS // THREADS

#update = lambda x : paper_info_db_check_multiquery(x, force=True)

def update(paper_in):
    papers, all_papers = paper_in

    print(os.getpid(), 'updating', papers)

    total_res, partial_res = paper_info_multiquery(papers, force=True)

    cache_paper_info(total_res)

    print([p['PaperId'] for p in total_res])
    missing_papers = set(papers)
    for paper_info in total_res:
        missing_papers.remove(paper_info['PaperId'])

    partial_uniq = [p for p in partial_res if p['PaperId'] not in all_papers]
    cache_paper_info(partial_res)

    return missing_papers

pool = Pool(THREADS)

# Elastic search client
client = Elasticsearch(conf.get("elasticsearch.hostname"))

'''
update(([1519075555], [1519075555]))

'''
while True:
    paper_info_s = Search(index='paper_info', using=client)
    #paper_info_s = paper_info_s.query('')
    paper_info_s = paper_info_s.source('PaperId')
    paper_info_s = paper_info_s.sort({ "CreatedDate": { "order": "asc" } })

    results = paper_info_s[:NUM_PAPERS]

    papers = [x.PaperId for x in results.execute()]

    vals = list()
    for i in range(THREADS):
        t_papers = papers[i * PER_THREAD: min((i+1) * PER_THREAD, NUM_PAPERS)]
        vals.append((t_papers, papers))
        #x = pool.apply_async(update, (t_papers))

    res = pool.map(update, vals)
    missing = set()
    for r in res:
        missing.update(r)

    print()
    print(missing)

    missing_s = Search(index='paper_info', using=client)
    missing_s = missing_s.query('terms', PaperId=list(missing))

    repost = list()
    for paper_info in missing_s.scan():
        paper_info = paper_info.to_dict()
        del paper_info['CreatedDate']

        repost.append(paper_info)

    cache_paper_info(repost)
