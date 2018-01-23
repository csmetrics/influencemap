import json
import os

CONFIG_NAME = 'config.json'
CONFIG_PATH = os.path.join(os.path.dirname(__file__), CONFIG_NAME)

def set_path(path):
    #if not os.path.exists(path):
    #    os.makedirs(path)
    #os.chmod(path, 0o777)
    return path

# Config setup
with open(CONFIG_PATH) as config_data:
    config = json.load(config_data)

    BATCH_SIZE = config['sqlite3']['batch size']
    DB_DIR = config['sqlite3']['directory']
    DB_PATH = os.path.join(DB_DIR, config['sqlite3']['name'])

    OUT_DIR = set_path(config['data']['out'])

    CACHE_DIR = set_path(config['cache']['directory']['main'])
    DATA_CACHE = set_path(os.path.join(CACHE_DIR, config['cache']['directory']['data']))
    REF_CACHE = set_path(os.path.join(CACHE_DIR, config['cache']['directory']['ref']))
    INFO_CACHE = set_path(os.path.join(CACHE_DIR, config['cache']['directory']['info']))
    PAPER_THRESHOLD = config['cache']['paper threshold']

    NUM_LEAVES = config['flower']['leaves']
