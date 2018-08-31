'''
Functions for querying MAG API to get paper information fields.
Aimed to provide caching in ES.

date:   25.06.18
author: Alexander Soen
'''

import copy

from core.config import *
from core.search.mag_interface import *
from core.search.query_info_db import papers_prop_query
from core.search.query_info_cache import base_paper_cache_query
from core.search.parse_academic_search import or_query_builder

MAS_URL_PREFIX  = "https://api.labs.cognitive.microsoft.com"
API_CHUNK_SIZE = 1000

basic_attr = {'Id': 'PaperId',
              'Y' : 'Year',
              'Ti': 'PaperTitle'}

compound_attr = {
             'C': {
                'CId': 'ConferenceSeriesId',
                'CN' : 'ConferenceName',
                },
             'J': {
                'JId': 'JournalId',
                'JN' : 'JournalName',
                },
             'AA': {
                'AuId': 'AuthorId',
                'AuN' : 'AuthorName',
                'AfId': 'AffiliationId',
                'AfN' : 'AffiliationName',
                },
             'F': {
                'FId': 'FieldOfStudyId',
                'FN' : 'FieldOfStudyName',
                }
             }

list_attr_names = {'AA': 'Authors',
                   'F' : 'FieldOfStudy'}

# Create search
compound_snames = list(basic_attr.keys())
for attr_type, attr in compound_attr.items():
    # Create name to search
    to_name = lambda x: '.'.join([attr_type, x])
    compound_snames += list(map(to_name, attr.keys()))
# Turn into string
compound_snames = ','.join(compound_snames)


def base_paper_mag_multiquery(paper_ids):
    ''' Returns all basic fields of a paper with API.
    '''
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    query = lambda x: {
        'expr': or_query_builder('Id={}', paper_ids),
        'count': 10000,
        'offset': x,
        'attributes': compound_snames
        }

    # Query result
    results = dict()

    # Checking offsets
    finished = False
    count    = 0

    while not finished:
        data = query_academic_search('post', url, query(count))

        # Check if no more data
        if len(data['entities']) > 0:
            count += len(data['entities'])
        else:
            finished = True

        for res in data['entities']:
            res_row = dict()

            # Get basic attributes
            for a, n in basic_attr.items():
                if a in res:
                    res_row[n] = res[a]

            # Get compound attributes
            for t, ca in compound_attr.items():
                # Check if result exists for type
                if t not in res:
                    continue

                # If field type, need to process list
                if t in list_attr_names.keys():
                    attr_res = list()

                    # Go through each value in list
                    for a_dict in res[t]:
                        suba_dict = dict()
                        # Get values for single entry
                        for a, n in ca.items():
                            if a in a_dict:
                                suba_dict[n] = a_dict[a]

                        attr_res.append(suba_dict)

                    # Add field
                    res_row[list_attr_names[t]] = attr_res

                # Other singular types
                else:
                    for a, n in ca.items():
                        try:
                            res_row[n] = res[t][a]
                        except KeyError:
                            pass

            # Add paper
            results[res['Id']] = res_row

    # Return results
    return results


def pr_links_mag_multiquery(paper_ids):
    ''' Get the citation links for a paper in paper information format.
    '''
    # Query results
    results = dict()

    # Initalise results
    for paper_id in paper_ids:
        results[int(paper_id)] = {'References': list(), 'Citations': list()}

    # Calculate references
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    query = lambda x: {
        'expr': or_query_builder('Id={}', paper_ids),
        'count': 10000,
        'offset': x,
        'attributes': 'RId'
        }

    # Checking offsets
    finished = False
    count    = 0

    while not finished:
        data = query_academic_search('post', url, query(count))

        # Check if no more data
        if len(data['entities']) > 0:
            count += len(data['entities'])
        else:
            finished = True

        # Add references
        for res in data['entities']:
            if 'RId' in res:
                results[res['Id']]['References'] += res['RId']

    for paper_id in paper_ids:
        # Checking offsets
        finished = False
        count    = 0

        while not finished:
            query = lambda x: {
            'expr': 'RId={}'.format(paper_id),
            'count': 10000,
            'offset': x,
            'attributes': 'Id,RId'
            }

            data = query_academic_search('post', url, query(count))

            # Check if no more data
            if len(data['entities']) > 0:
                count += len(data['entities'])
            else:
                finished = True

            # Add citations
            for res in data['entities']:
                if 'RId' in res:
                    for rid in res['RId']:
                        if rid in paper_ids:
                            results[rid]['Citations'].append(res['Id'])

    # Remove doubles
    for paper_id, cite_dict in results.items():
        results[paper_id]['Citations'] = list(set(cite_dict['Citations']))

    return results


def paper_info_mag_multiquery(paper_ids, partial_info = list()):
    ''' Find paper information with MAG, "optimised"
    '''
    paper_props = dict()
    # Turn partial info into a map
    for p_info in partial_info:
        paper_props[p_info['PaperId']] = p_info

    # Get union of paper info ids to generate
    paper_ids_union = list(set(paper_ids + list(paper_props.keys())))
        
    # Get paper links
    paper_links = pr_links_mag_multiquery(paper_ids_union)

    # Link papers
    link_papers = list()
    for paper_link in paper_links.values():
        link_papers += paper_link['References'] + paper_link['Citations']
    link_papers = list(set(link_papers) - set(paper_props.keys()))

    # In cache list to ensure no overrides
    in_cache = list()

    # Get all papers to get property values
    all_papers = list() + paper_ids
    for link_paper in link_papers:
        link_prop = base_paper_cache_query([link_paper])[0]
        if link_prop:
            paper_props[link_paper] = link_prop
            in_cache.append(link_paper)
        else:
            all_papers.append(link_paper)
    all_papers = list(set(all_papers))

    print("Number of paper props to get:", len(all_papers))
    # Find all basic properties of all the papers
    for chunk in [all_papers[i:i+API_CHUNK_SIZE] for i in
                  range(0, len(all_papers), API_CHUNK_SIZE)]:
        paper_props.update(base_paper_mag_multiquery(chunk))

    # Add properties to links
    paper_prop_links = dict()
    for paper_id, links in paper_links.items():
        link_res = dict()

        # For each type of link
        for link_type, link_papers in links.items():
            link_type_res = list()

            # Iterate through the link papers to get properties
            for link_paper in link_papers:
                if link_paper in paper_props:
                    link_type_res.append(paper_props[link_paper])

            # Add result of link type
            link_res[link_type] = link_type_res

        # Add to updated links
        paper_prop_links[paper_id] = link_res

    # Turn into paper_info dictionaries
    paper_info_res = list()
    partial_res    = list()
    
    for paper_id, paper_prop in paper_props.items():
        if paper_id in paper_ids_union:
            try:
                # Combine queries
                paper_prop['cache_type'] = 'complete'
                paper_link = copy.deepcopy(paper_prop_links[paper_id])
                paper_info_res.append(dict(paper_prop, **paper_link))
            except KeyError:
                pass
        else:
            # If not already in cache
            if not paper_id in in_cache:
                paper_prop['cache_type'] = 'partial'
                partial_res.append(paper_prop)

    return paper_info_res, partial_res
