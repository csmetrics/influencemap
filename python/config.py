import json

def set_path(path):
    if not os.path.exists(path):
          os.makedirs(path)
    return path

# Config setup
with open('config.json') as config_data:
    config = json.load(config_data)
    DB_DIR = config['sqlite3']['directory']
    DB_PATH = os.path.join(DB_DIR, config['sqlite3']['name'])
    OUT_DIR = set_path(config['data']['out'])
    NUM_LEAVES = config['flower']['leaves']
    BATCH_SIZE = config['sqlite3']['batch size']
    CACHE_DIR = set_path(config['cache']['directory'])
