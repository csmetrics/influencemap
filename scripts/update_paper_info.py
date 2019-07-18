#%%
# Imports
import os
import json

from datetime import datetime

from graph.config import conf
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q

from core.search.query_info_db import paper_info_multiquery
from core.search.cache_data import cache_paper_info

#%%
# Consts
SCRIPT_CONFIG = 'script_config.json'

START_VERSION = 0
THREADS = 1
BATCH_SIZE = 10

#%%
# Try load config
try:
    config_path = os.path.join('scripts', SCRIPT_CONFIG)

    with open(config_path, 'r') as f:
        config = json.load(f)
        START_VERSION = config['update_version']
        THREADS = config['threads']
        BATCH_SIZE = config['batch_size']
except FileExistsError:
    pass

#%%
# Elastic search client
client = Elasticsearch(conf.get('elasticsearch.hostname'))

#%%
query = Q('bool',
        should=[~ Q('exists', field='UpdateVersion'), Q('range', UpdateVersion={'lt': START_VERSION})],
        minimum_should_match=1
        )

cache_allow = Q('bool',
        must=[Q('exists', field='UpdateVersion'), Q('range', UpdateVersion={'gte': START_VERSION})],
        minimum_should_match=1
        )

#%%
counter = 1
while True:
    print('\n[{}] - Start batch {}'.format(datetime.now(), counter))
    paper_info_s = Search(index='paper_info', using=client)
    paper_info_s = paper_info_s.source('PaperId')
    paper_info_s = paper_info_s.sort({ 'CreatedDate': { 'order': 'desc' } })
    paper_info_s = paper_info_s.query(query)

    print('[{}] -- Find papers to update'.format(datetime.now()))
    paper_ids = [p.PaperId for p in paper_info_s.execute()]
    print(paper_ids[0])

    if not paper_ids:   
        break

    print('[{}] -- Generate cache entries'.format(datetime.now()))
    total_res, partial_res = paper_info_multiquery(paper_ids, query_filter=cache_allow)

    print('[{}] -- Add to cache'.format(datetime.now()))
    cache_paper_info(total_res, additional_tag={'UpdateVersion': START_VERSION})
    cache_paper_info(partial_res, additional_tag={'UpdateVersion': START_VERSION})

    print('[{}] - Finish batch {}\n'.format(datetime.now(), counter))
    counter += 1