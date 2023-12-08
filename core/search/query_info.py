import requests

OPENALEX_URL = "https://api.openalex.org"


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


def query_entities_by_list(type, type_str, eids):
    params = {
        'filter': 'ids.openalex:'+'|'.join(['https://openalex.org/{}{}'.format(type_str, eid) for eid in eids]),
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


def query_entity_by_id(type, type_str, id):  # For test purpose
    try:
        path = "{}/{}/{}{}".format(OPENALEX_URL, type, type_str, str(id))
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

    # Targets
    papers_targets = ['DocType', 'OriginalTitle', 'OriginalVenue', 'Year']

    # raise Exception(len(paper_ids), paper_ids)
    # Query for papers
    papers_s = {mag_id: query_openalex_by_mag_id(
        mag_id) for mag_id in paper_ids}

    # Convert papers into dictionary format
    results = dict()
    for p_id, paper in papers_s.items():
        try:
            try:
                venue = paper['primary_location']['source']['host_organization_name']
            except Exception:
                venue = None

            results[p_id] = {
                'PaperId': p_id,
                'OriginalTitle': paper['title'],
                'OriginalVenue': venue,
                'Year': paper['publication_year']
            }
        except Exception:
            raise Exception(p_id, paper)

    return results
