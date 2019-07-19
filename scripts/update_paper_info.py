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
complete_updated = 0
partial_updated = 0
removed = 0
while True:
    print('\n[{}] - Start batch {}'.format(datetime.now(), counter))
    paper_info_s = Search(index='paper_info', using=client)
    paper_info_s = paper_info_s.source(['PaperId', 'cache_type'])
    paper_info_s = paper_info_s.sort({ 'CreatedDate': { 'order': 'desc' } })
    paper_info_s = paper_info_s.query(query)

    print('[{}] -- Find papers to update'.format(datetime.now()))
    paper_ids = [(p.PaperId, p.cache_type) for p in paper_info_s.execute()]
    print(paper_ids[0])

    if not paper_ids:   
        break

    complete_papers = [p for (p, t) in paper_ids if t == 'complete']
    partial_papers = [p for (p, t) in paper_ids if t == 'partial']

    print('[{}] -- Generate cache entries'.format(datetime.now()))
    complete_res, partial_res = paper_info_multiquery(complete_papers, query_filter=cache_allow, partial_updates=partial_papers ,recache=True)

    print('[{}] -- Add to cache'.format(datetime.now()))
    cache_paper_info(complete_res, additional_tag={'UpdateVersion': START_VERSION})
    cache_paper_info(partial_res, additional_tag={'UpdateVersion': START_VERSION})

    print('[{}] -- Remove old paper ids'.format(datetime.now()))
    res_ids = [p['PaperId'] for p in complete_res + partial_res]
    old_ids = [p for p in next(zip(*paper_ids)) if p not in res_ids]
    if len(old_ids) > 0:
        remove_s = Search(index='paper_info', using=client)
        remove_s = remove_s.query('terms', PaperId=old_ids)
        remove_s.delete()

    print('[{}] - Finish batch {}\n'.format(datetime.now(), counter))
    counter += 1
    complete_updated += len(complete_res)
    partial_updated += len(partial_res)
    removed += len(old_ids)

    print('\n[{}] - Complete: {}, Partial: {}, Total: {}, Remove: {}\n'.format(
        datetime.now(), complete_updated, partial_updated, complete_updated +
        partial_updated, removed))
