import requests

WORK_FILTER_URL_MAG = "https://api.openalex.org/works"

def query_openalex_by_mag_id(mag_id):
    params = {
        'filter': 'ids.mag:'+mag_id,
        'mailto': 'minjeong.shin@anu.edu.au'
    }
    try:
        response = requests.get(WORK_FILTER_URL_MAG, params=params)
        if response.status_code == 200:
            data = response.json()
            return data['results'][0]
        else:
            print("[query_openalex_by_mag_id] Request failed with status code:", response.status_code)
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
    papers_s = {mag_id:query_openalex_by_mag_id(mag_id) for mag_id in paper_ids}

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