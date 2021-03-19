
#%%
# Imports
import os
import json

from datetime import datetime

from graph.config import conf
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q

from core.search.query_info import paper_info_db_check_multiquery

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
        print(BATCH_SIZE)
except FileExistsError:
    pass

#%%
# Elastic search client
client = Elasticsearch(conf.get('elasticsearch.hostname'))

#%%
counter = 1
complete_updated = 0
while True:
    print('\n[{}] - Start batch {}'.format(datetime.now(), counter))
    paper_ids_s = Search(index='papers', using=client)
    paper_ids_s = paper_ids_s.source(['PaperId'])
    paper_ids_s_res = paper_ids_s[:BATCH_SIZE]

    print('[{}] -- Find papers to update'.format(datetime.now()))
    paper_ids = [p.PaperId for p in paper_ids_s_res.execute()]
    print(len(paper_ids))

    if not paper_ids:
        break

    print('[{}] -- Generate cache entries'.format(datetime.now()))
    complete_res = paper_info_db_check_multiquery(paper_ids)

    print('[{}] - Finish batch {}\n'.format(datetime.now(), counter))
    counter += 1
    complete_updated += len(complete_res)

    print('\n[{}] - Complete: {}\n'.format(
        datetime.now(), complete_updated))
