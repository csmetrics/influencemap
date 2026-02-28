import requests
import os
import pathlib

# Try to load OPENALEX_KEY from a .env file (use python-dotenv if available,
# otherwise search up from this file's directory).
def _load_openalex_key():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        p = pathlib.Path(__file__).resolve()
        for _ in range(6):
            env_file = p.parent / '.env'
            if env_file.exists():
                with env_file.open() as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if '=' in line:
                            k, v = line.split('=', 1)
                            k = k.strip()
                            v = v.strip().strip('"').strip("'")
                            os.environ.setdefault(k, v)
                break
            if p.parent == p:
                break
            p = p.parent

_load_openalex_key()
OPENALEX_KEY = os.environ.get('OPENALEX_KEY')

def _params_with_key(params=None):
    params = dict(params) if params else {}
    if OPENALEX_KEY:
        params['api_key'] = OPENALEX_KEY
    return params

def _get(url, params=None, **kwargs):
    return requests.get(url, params=_params_with_key(params), **kwargs)

OPENALEX_URL = "https://api.openalex.org"

openalex_splitter = {
    'authors': 'A',
    'institutions': 'I',
    'sources': 'S',
    'works': 'W',
    'concepts': 'C',
}


def convert_id(id, type):
    return int(id.split(openalex_splitter[type])[-1])


def query_entity_by_keyword(entity_types, entity_title):
    res = []
    for etype in entity_types:
        try:
            params = {
                'search': entity_title,
                'mailto': 'minjeong.shin@anu.edu.au'
            }
            if etype == 'works':
                params['filter'] = "title.search:{}".format(entity_title)
            response = _get(OPENALEX_URL+"/"+etype, params=params)
            # print(response.url)
            if response.status_code == 200:
                data = response.json()
                res.extend([(d, etype) for d in data['results']])
            else:
                print("[query_entity_by_id] Request failed with status code:",
                      response.status_code)
        except requests.exceptions.RequestException as e:
            print("[query_entity_by_id] An error occurred:", e)

    return res


def query_entities_by_list(type, eids):
    params = {
        'filter': 'ids.openalex:'+'|'.join(['https://openalex.org/{}{}'.format(
            openalex_splitter[type], eid) for eid in eids]),
        'per-page': len(eids),
        'mailto': 'minjeong.shin@anu.edu.au'
    }
    try:
        response = _get(OPENALEX_URL+"/"+type, params=params)
        # print(response.url)
        if response.status_code == 200:
            data = response.json()
            return data['results']
        else:
            print("[query_entity_by_id] Request failed with status code:",
                  response.status_code)
    except requests.exceptions.RequestException as e:
        print("[query_entity_by_id] An error occurred:", e)
    return []


def query_entity_by_id(type, id):  # For test purpose
    try:
        path = "{}/{}/{}{}".format(OPENALEX_URL, type,
                                   openalex_splitter[type], str(id))
        print(path)
        response = _get(path)
        if response.status_code == 200:
            data = response.json()
            print("query_entity_by_id", id, data['display_name'])
            return data['display_name']
        else:
            print("[query_entity_by_id] Request failed with status code:",
                  response.status_code)
    except requests.exceptions.RequestException as e:
        print("[query_entity_by_id] An error occurred:", e)
    return None 


def papers_prop_query(paper_ids):
    ''' Get properties of a paper.
    '''

    # Query for papers
    papers_s = query_entities_by_list("works", paper_ids)

    # Convert papers into dictionary format
    results = dict()
    for paper in papers_s:
        try:
            try:
                venue = paper['primary_location']['source']['display_name']
            except Exception:
                venue = ''

            p_id = convert_id(paper['id'], "works")
            results[p_id] = {
                'PaperId': p_id,
                'OriginalTitle': paper['title'],
                'OriginalVenue': venue,
                'Year': paper['publication_year']
            }
        except Exception:
            raise Exception(paper)

    return results
