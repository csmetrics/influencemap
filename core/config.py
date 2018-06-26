import json
import os, re

CONFIG_NAME = 'config.json'
CONFIG_PATH = os.path.join(os.path.dirname(__file__), CONFIG_NAME)

def set_path(path):
    #if not os.path.exists(path):
    #    os.makedirs(path)
    #os.chmod(path, 0o777)
    return path

# Config setup
try:
    with open(CONFIG_PATH) as config_data:
        config = json.load(config_data)

        #BATCH_SIZE = config['sqlite3']['batch size']
        #DB_DIR = config['sqlite3']['directory']
        #DB_PATH = os.path.join(DB_DIR, config['sqlite3']['name'])

        #OUT_DIR = set_path(config['data']['out'])

        CACHE_PAPERS_DIR = set_path(config['cache']['directory']['papers'])
        CACHE_INFLUENCE_DIR = set_path(config['cache']['directory']['influence'])
        CACHE_SCORE_DIR = set_path(config['cache']['directory']['score'])
        #PAPER_THRESHOLD = config['cache']['paper threshold']

        NUM_LEAVES = config['flower']['leaves']

        # MAG API
        MAG_URL_PREFIX = config['mag_api']['prefix']
        JSON_URL = os.path.join(MAG_URL_PREFIX, config['mag_api']['json_postfix'])

        # API key setup
        API_KEYS = [line.strip() for line in open(config['mag_api']['api_key_dir'], 'r')]
        key_filter = re.compile(r'[a-z0-9]{32}')
        API_KEYS = list(filter(key_filter.search, API_KEYS))
        MAX_API  = len(API_KEYS)

        API_RES_COUNT = config['mag_api']['res_count']

except Exception as e:
    print("===========================================================")
    print("Failed to read config_data. Enter Developer mode.")
    print("API will NOT work, but you are still able to develop front end.")
    print("===========================================================")
    API_KEYS = ["No Key" for r in range(10)]
