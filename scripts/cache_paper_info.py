
#%%
# Imports
import os
import json

from datetime import datetime

from elasticsearch_dsl import Search, Q

from core.elastic import client
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
counter = 0
complete_updated = 0

print('\n[{}] - Start batch {}'.format(datetime.now(), counter))
paper_ids_s = Search(index='papers', using=client)
paper_ids_s = paper_ids_s.source(['PaperId'])
# paper_ids_s = paper_ids_s.params(size=BATCH_SIZE)

print('[{}] -- Find papers to update'.format(datetime.now()))
for p in paper_ids_s.scan():
    paper_ids = [p.PaperId]
    print(paper_ids)
    # print("{}: from {} to {}".format(len(paper_ids), paper_ids[0], paper_ids[-1]))

    if not paper_ids:
        break

    print('[{}] -- Generate cache entries'.format(datetime.now()))
    complete_res = paper_info_db_check_multiquery(paper_ids)

    print('[{}] - Finish batch {}\n'.format(datetime.now(), counter))
    counter += 1
    complete_updated += len(complete_res)

    print('\n[{}] - Complete: {}\n'.format(
        datetime.now(), complete_updated))
