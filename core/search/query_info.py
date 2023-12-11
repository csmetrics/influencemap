import requests

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
            response = requests.get(OPENALEX_URL+"/"+etype, params=params)
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
        response = requests.get(OPENALEX_URL+"/"+type, params=params)
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
        response = requests.get(path)
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


def query_openalex_by_mag_id(mag_id):
    params = {
        'filter': 'ids.mag:'+mag_id,
        'mailto': 'minjeong.shin@anu.edu.au'
    }
    try:
        response = requests.get(OPENALEX_URL+"/works", params=params)
        if response.status_code == 200:
            data = response.json()
            return data['results'][0]
        else:
            print("[query_openalex_by_mag_id] Request failed with status code:",
                  response.status_code)
    except requests.exceptions.RequestException as e:
        print("[query_openalex_by_mag_id] An error occurred:", e)
    return {}


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
                venue = paper['primary_location']['source']['host_organization_name']
            except Exception:
                venue = None

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
