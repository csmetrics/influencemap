'''
Functions for querying MAG API to get paper information fields.
Aimed to provide caching in ES.

date:   25.06.18
author: Alexander Soen
'''

from core.config import *
from core.search.mag_interface import *
from core.search.query_info_db import papers_prop_query
from core.search.parse_academic_search import or_query_builder_list

MAS_URL_PREFIX = "https://api.labs.cognitive.microsoft.com"

def papers_prop_mag_multiquery(paper_ids):
    '''
    '''
    print("TEST", len(paper_ids))
    # Query
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    queries = ({
        'expr': expr,
        'count': 1000,
        'offset': 0,
        'attributes': 'Id, Y, C.CId, J.JId'
        } for expr in or_query_builder_list('Id={}', paper_ids))

    # Query result
    result = dict()

    for query in queries:
        print(query)
        data = query_academic_search('get', url, query)

        for res in data['entities']:
            res_row = dict()

            # Set name
            res_row['PaperId'] = res['Id']
            try:
                res_row['Year'] = res['Y']
            except KeyError:
                pass

            try:
                res_row['ConferenceSeriesId'] = res['C.CId']
            except KeyError:
                pass

            try:
                res_row['JournalId'] = res['J.JId']
            except KeyError:
                pass

            result[res['Id']] = res_row

    return result


def paa_prop_mag_multiquery(paper_ids):
    ''' Get the authors for a paper in paper information format.
    '''
    # Query
    query = {
        'path': '/paper',
        'paper': {
            'type': 'Paper',
            'id': paper_ids,
            'select': [
                    'AuthorIDs',
                    'AffiliationIDs'
                ]
            }
        }

    # Call to API
    data = query_academic_search('post', JSON_URL, query)

    # Query results
    paa_res_dict = dict()

    # Check for empty results
    if not data['Results']:
        return paa_res_dict

    # Initialise results
    for paper_id in paper_ids:
        paa_res_dict[paper_id] = {'Authors': list()}

    # Iterate through the results
    for results in data['Results']:
        res_row = list()
        paper_res = results[0]

        # Covert into authors object in ES
        paa = zip(paper_res['AuthorIDs'], paper_res['AffiliationIDs'])
        for author, affiliation in paa:
            paa_row = dict()
            paa_row['AuthorId']      = author
            paa_row['AffiliationId'] = affiliation

            res_row.append(paa_row)

        paa_res_dict[paper_res['CellID']] = {'Authors': res_row}

    return paa_res_dict


def pr_links_mag_multiquery(paper_ids):
    ''' Get the citation links for a paper in paper information format.
    '''
    
    # Query
    ref_query = {
        'path': '/paper/ReferenceIDs/cites',
        'paper': {
            'type': 'Paper',
            'id': paper_ids,
            }
        }

    cite_query = {
        'path': '/paper/CitationIDs/cites',
        'paper': {
            'type': 'Paper',
            'id': paper_ids,
            }
        }

    # Query results
    results = dict()

    # Initalise results
    for paper_id in paper_ids:
        results[paper_id] = {'References': list(), 'Citations': list()}
        

    # Call to API
    ref_data = query_academic_search('post', JSON_URL, ref_query)
    cite_data = query_academic_search('post', JSON_URL, cite_query)

    # Add references and citations to results
    for ego, other in ref_data['Results']:
        results[ego['CellID']]['References'].append(other['CellID'])

    for ego, other in cite_data['Results']:
        results[ego['CellID']]['Citations'].append(other['CellID'])

    return results


def base_paper_mag_multiquery(paper_ids):
    '''
    '''
    # Author information
    paa_props = paa_prop_mag_multiquery(paper_ids)

    base_res   = dict()
    to_process = dict()

    # Get properties for each author information dictionaries
    for paper_id, auth_dict in paa_props.items():
        paper_props = papers_prop_query(paper_id)
        if not paper_props:
            print(paper_id, "Failed ES lookup on index 'Papers'")
            to_process[paper_id] = auth_dict
        else:
            base_res[paper_id] = dict(paper_props, **auth_dict)

    # Get from MAG now
    processed_props = papers_prop_mag_multiquery(list(to_process.keys()))
    for paper_id, auth_dict in to_process.items():
        try:
            paper_props = processed_props[paper_id]
            base_res[paper_id] = dict(paper_props, **auth_dict)
        except KeyError:
            pass

    return base_res


def link_paper_info_mag_multiquery(paper_ids):
    '''
    '''

    # Get citation links
    pr_link_dict = pr_links_mag_multiquery(paper_ids)

    # Query results
    link_paper_res  = dict()
    link_cache_dict = dict()

    for paper_id, pr_links in pr_link_dict.items():

        # Results per paper
        link_res = dict()

        # Iterate through the link types
        for link_type, link_papers in pr_links.items():

            # Initialise the type result
            link_res[link_type] = list()
            to_process          = list()

            for link_paper in link_papers:
                try:
                    link_cache_dict[link_type].append(link_paper)
                except:
                    to_process.append(link_paper)

            # Resulting link results
            link_vals = base_paper_mag_multiquery(to_process)
            link_cache_dict.update(link_vals)
            link_res[link_type] += list(link_vals.values())

        # Add to final result
        link_paper_res[paper_id] = link_res

    return link_paper_res


def paper_info_mag_multiquery(paper_ids):
    '''
    '''
    # Query basic properties
    paper_bases = base_paper_mag_multiquery(paper_ids)
    paper_links = link_paper_info_mag_multiquery(paper_ids)

    # Combine queries
    paper_info_res = list()
    for paper_id, paper_base in paper_bases.items():
        paper_info_res.append(dict(paper_base, **paper_links[paper_id]))

    return paper_info_res


if __name__ == '__main__':
    # TEST
#    print(paa_prop_multiquery([2279671314]))
    print(pr_links_mag_multiquery([2279671314]))
