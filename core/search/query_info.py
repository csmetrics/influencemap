'''
Functions which combines the different query functions in query_db and
query_cache.

date:   24.06.18
author: Alexander Soen
'''

import copy
from datetime import datetime

from core.search.elastic import client
from core.search.query_info_cache import base_paper_cache_query
from core.search.query_name import *

from core.search.cache_data       import cache_paper_info
from core.search.query_info_cache import paper_info_cache_query
from core.search.query_utility    import chunker
from itertools import zip_longest

from elasticsearch_dsl import Search, Q
from graph.config import conf

TIMEOUT = 60

def paper_info_db_check_multiquery(paper_ids, force=False):
    ''' Query which checks cache for existence first. Otherwise tries to
        generate paper info from basic tables and adds to cache.
    '''
    # Find entries in ES
    if force:
        to_add_links   = list()
        to_process     = paper_ids
        paper_info_res = list()
    else:
        es_res = paper_info_cache_query(paper_ids)
        to_add_links   = es_res['partial']
        to_process     = list(es_res['missing'])
        paper_info_res = es_res['complete']

    print("Complete cache entries found:", len(paper_info_res))
    print("Partial cache entries found:", len(to_add_links))
    print("No cache entries found:", len(to_process))
    print("Total ids to query:", len(paper_ids))

    # Check if items do not exist in cache
    if to_process or to_add_links:
        total_res, partial_res = paper_info_multiquery(to_process,
                                       partial_info=to_add_links,
                                       force=force)

        complete_res = [t for t in total_res if t['cache_type'] == 'complete']
        print("Total entries found:", len(total_res))
        print("Complete cached:", len(complete_res))
        print("Partial cached:", len(partial_res))

        # Cache
        cache_paper_info(complete_res)
        cache_paper_info(partial_res, chunk_size=100)
        paper_info_res += total_res

    return paper_info_res

def papers_prop_query(paper_ids):
    ''' Get properties of a paper.
    '''
    # Targets
    papers_targets = ['DocType', 'OriginalTitle', 'OriginalVenue', 'Year']

    # Query for papers
    papers_s = Search(index = conf.get('index.paper'), using = client)
    papers_s = papers_s.query('terms', PaperId=paper_ids)
    papers_s = papers_s.source(papers_targets)
    papers_s = papers_s.params(request_timeout=TIMEOUT)

    # Convert papers into dictionary format
    results = dict()
    conf_ids = set()
    jour_ids = set()
    for paper in papers_s.scan():
        # Get properties for papers
        paper_res = paper.to_dict()
        p_id = int(paper.meta.id)
        paper_res['PaperId'] = p_id
        results[p_id] = paper_res

    return results


def paa_prop_query(paper_ids):
    ''' Get properties of a paper.
    '''
    # Targets
    paa_targets = ['PaperId', 'AuthorId', 'AffiliationId']

    # Query for paper affiliation
    paa_s = Search(index = conf.get('index.paa'), using = client)
    paa_s = paa_s.query('terms', PaperId=paper_ids)
    paa_s = paa_s.source(paa_targets)
    paa_s = paa_s.params(request_timeout=TIMEOUT)

    # Convert paa into dictionary format
    results = dict()
    auth_ids = set()
    affi_ids = set()
    for paa in paa_s.scan():
        paa_res = paa.to_dict()

        # Get fields
        paper_id = paa_res['PaperId']
        del paa_res['PaperId']

        # Author
        if 'AuthorId' in paa_res:
            auth_ids.add(paa_res['AuthorId'])

        # Affiliation
        if 'AffiliationId' in paa_res:
            affi_ids.add(paa_res['AffiliationId'])

        # Aggregate results
        if paper_id in results:
            results[paper_id].append(paa_res)
        else:
            results[paper_id] = [paa_res]

    auth_names = author_name_dict_query(list(auth_ids))
    affi_names = affiliation_name_dict_query(list(affi_ids))

    res = dict()
    for p_id, paa_info_list in results.items():
        paa_res = list()
        for paa_info in paa_info_list:
            if 'AuthorId' in paa_info:
                if paa_info['AuthorId'] in auth_names:
                    paa_info['AuthorName'] = auth_names[paa_info['AuthorId']]
                else:
                    continue

            if 'AffiliationId' in paa_info:
                if paa_info['AffiliationId'] in affi_names:
                    paa_info['AffiliationName'] = affi_names[paa_info['AffiliationId']]
                else:
                    continue

            paa_res.append(paa_info)

        res[p_id] = paa_res

    # Return as dictionary
    return res


def pfos_prop_query(paper_ids):
    ''' Get properties of a paper.
    '''
    # Targets
    pfos_targets = ['PaperId', 'FieldOfStudyId']

    # Query for paper affiliation
    pfos_s = Search(index = conf.get('index.pfos'), using = client)
    pfos_s = pfos_s.query('terms', PaperId=paper_ids)
    pfos_s = pfos_s.source(pfos_targets)
    pfos_s = pfos_s.params(request_timeout=TIMEOUT)

    # Convert paa into dictionary format
    results = dict()
    fos_ids = set()
    for pfos in pfos_s.scan():
        pfos_res = pfos.to_dict()

        # Get fields
        paper_id = pfos_res['PaperId']
        del pfos_res['PaperId']

        # Author
        if 'FieldOfStudyId' in pfos_res:
            fos_ids.add(pfos_res['FieldOfStudyId'])

        # Aggregate results
        if paper_id in results:
            results[paper_id].append(pfos_res)
        else:
            results[paper_id] = [pfos_res]

    fos_names, fos_levels = fos_name_level_dict_query(list(fos_ids))

    res = dict()
    for p_id, pfos_info_list in results.items():
        pfos_res = list()
        for pfos_info in pfos_info_list:
            if 'FieldOfStudyId' in pfos_info:
                if pfos_info['FieldOfStudyId'] in fos_names:
                    pfos_info['FieldOfStudyName'] = fos_names[pfos_info['FieldOfStudyId']]
                    pfos_info['FieldOfStudyLevel'] = fos_levels[pfos_info['FieldOfStudyId']]
                else:
                    continue
            pfos_res.append(pfos_info)

        res[p_id] = pfos_res

    # Return as dictionary
    return res



def pr_links_query(paper_ids):
    ''' Get properties of a paper.
    '''
    # Targets
    pr_targets = ['PaperId', 'PaperReferenceId', 'FieldOfStudyId']

    # Query results
    references = list()
    citations  = list()
    fieldsofstudy = list()

    # Result dictionary
    results = dict()
    for paper_id in paper_ids:
        results[paper_id] = {'References': [], 'Citations': [], 'FieldsOfStudy': []}

    # Query for paper references
    ref_s = Search(index = conf.get('index.pref'), using = client)
    ref_s = ref_s.query('terms', PaperId=paper_ids)
    ref_s = ref_s.params(request_timeout=TIMEOUT)

    # Convert into dictionary format
    for ref_info in ref_s.scan():
        results[ref_info[pr_targets[0]]]['References'].append(ref_info[pr_targets[1]])

    # Query for paper citations
    cit_s = Search(index = conf.get('index.pref'), using = client)
    cit_s = cit_s.query('terms', PaperReferenceId=paper_ids)
    cit_s = cit_s.params(request_timeout=TIMEOUT)

    # Convert into dictionary format
    for cit_info in cit_s.scan():
        results[cit_info[pr_targets[1]]]['Citations'].append(cit_info[pr_targets[0]])

    # Query for paper fields of study
    fos_s = Search(index = conf.get('index.pfos'), using = client)
    fos_s = fos_s.query('terms', PaperId=paper_ids)
    fos_s = fos_s.params(request_timeout=TIMEOUT)

    # Convert into dictionary format
    for fos_info in fos_s.scan():
        results[fos_info[pr_targets[0]]]['FieldsOfStudy'].append(fos_info[pr_targets[2]])

    # Return results as a dictionary
    return results


def base_paper_db_query(paper_ids):
    ''' Generates basic paper_info dictionary/json from basic databases (not
        cache).
    '''
    t_cur = datetime.now()
    # Get basic paper properties
    papers_props = papers_prop_query(paper_ids)
    print('Get basic props', datetime.now() - t_cur)

    t_cur = datetime.now()
    # Get author information
    paa_props = paa_prop_query(paper_ids)
    print('Get paa', datetime.now() - t_cur)

    t_cur = datetime.now()
    # Get fos information
    pfos_props = pfos_prop_query(paper_ids)
    print('Get pfos', datetime.now() - t_cur)

    # Create partial entry
    results = list()
    for paper_id in paper_ids:
        # Make partial result
        if paper_id in papers_props:
            partial_res = papers_props[paper_id]
            if paper_id in paa_props:
                partial_res['Authors'] = paa_props[paper_id]
            else:
                partial_res['Authors'] = list()

            if paper_id in pfos_props:
                partial_res['FieldsOfStudy'] = pfos_props[paper_id]
            else:
                partial_res['FieldsOfStudy'] = list()


            results.append(partial_res)

    return results


def paper_info_multiquery(
        paper_ids, partial_info=list(), force=False, query_filter=None,
        partial_updates=list(), recache=False):
    """
    """
    # Create partial information dictionary
    paper_partial = dict()
    for p_info in partial_info:
        paper_partial[p_info['PaperId']] = p_info

    # List of papers we are interested in returning total results
    search_papers = paper_ids + list(paper_partial.keys())

    t_cur = datetime.now()
    # Find all paper links
    paper_links = pr_links_query(search_papers)
    print('Get links', datetime.now() - t_cur)

    # Calculate papers to query es for partials
    find_partial = set(paper_ids + partial_updates)
    for paper_link in paper_links.values():
        find_partial.update(paper_link['References'])
        find_partial.update(paper_link['Citations'])
        #find_partial.update(paper_link['FieldsOfStudy'])

    print("Need to find,", len(find_partial))
    print(find_partial)

    # Get list of papers which are in cache
    from_cached = list()

    if not force:
        # Get partial information for papers from cache
        for p_info in base_paper_cache_query(
                list(find_partial), query_filter=query_filter):
            p_id = p_info['PaperId']
            find_partial.remove(p_id)
            paper_partial[p_id] = p_info
            if not recache:
                from_cached.append(p_id)

    # Get partial information from db
    for p_info in base_paper_db_query(list(find_partial)):
        #print(p_info)
        p_id = p_info['PaperId']
        find_partial.remove(p_id)
        paper_partial[p_id] = p_info

    print("Missing paper:", find_partial)

    # Generate results
    total_res   = list()
    partial_res = list()
    for p_id, p_partial in paper_partial.items():

        p_partial = copy.deepcopy(p_partial)

        # If links exists and is a search paper
        if p_id in search_papers and p_id in paper_links:
            p_partial['cache_type'] = 'complete'

            # Create references and citations for total paper
            p_links = {'References': [], 'Citations': []} #, 'FieldsOfStudy': []}

            for r_id in paper_links[p_id]['References']:
                if r_id in paper_partial:
                    p_links['References'].append(paper_partial[r_id])

            for c_id in paper_links[p_id]['Citations']:
                if c_id in paper_partial:
                    p_links['Citations'].append(paper_partial[c_id])

            #for f_id in paper_links[p_id]['FieldsOfStudy']:
            #    if f_id in paper_partial:
            #        p_links['FieldsOfStudy'].append(paper_partial[f_id])

            total_res.append(dict(p_partial, **p_links))
        # Otherwise just add as partial cache entry
        else:
            # Avoid recaching
            if p_id in from_cached:
                continue

            p_partial['cache_type'] = 'partial'
            partial_res.append(p_partial)

    return total_res, partial_res
