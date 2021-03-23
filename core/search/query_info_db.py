'''
Functions for querying database for specific information:
  - Author information (Create generator function to query papers?)
  - Paper information

Each query goes through a cache layer before presenting information.
Without Pandas.

date:   24.06.18
author: Alexander Soen
'''

import copy
from datetime import datetime

from core.elastic import client
from core.search.query_info_cache import base_paper_cache_query
from core.search.query_name_db import *

from elasticsearch_dsl import Search, Q

TIMEOUT = 60

def papers_prop_query(paper_ids):
    ''' Get properties of a paper.
    '''
    # Targets
    papers_targets = ['PaperTitle', 'ConferenceSeriesId', 'JournalId', 'Year']

    # Query for papers
    papers_s = Search(index = 'papers', using = client)
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

        # Rename Conference
        if 'ConferenceSeriesId' in paper_res:
            conf_ids.add(paper_res['ConferenceSeriesId'])

        # Journal
        if 'JournalId' in paper_res:
            jour_ids.add(paper_res['JournalId'])

        paper_res['PaperId'] = p_id
        results[p_id] = paper_res

    conf_names = conference_name_dict_query(list(conf_ids))
    jour_names = journal_name_dict_query(list(jour_ids))

    res = dict()
    for p_id, paper_info in results.items():
        if 'ConferenceSeriesId' in paper_info:
            paper_info['ConferenceName'] = conf_names[paper_info['ConferenceSeriesId']]

        if 'JournalId' in paper_info:
            paper_info['JournalName'] = jour_names[paper_info['JournalId']]

        res[p_id] = paper_info

    return res


def paa_prop_query(paper_ids):
    ''' Get properties of a paper.
    '''
    # Targets
    paa_targets = ['PaperId', 'AuthorId', 'AffiliationId']

    # Query for paper affiliation
    paa_s = Search(index = 'paperauthoraffiliations', using = client)
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
    pfos_s = Search(index = 'paperfieldsofstudy', using = client)
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
    ref_s = Search(index = 'paperreferences', using = client)
    ref_s = ref_s.query('terms', PaperId=paper_ids)
    ref_s = ref_s.params(request_timeout=TIMEOUT)

    # Convert into dictionary format
    for ref_info in ref_s.scan():
        results[ref_info[pr_targets[0]]]['References'].append(ref_info[pr_targets[1]])

    # Query for paper citations
    cit_s = Search(index = 'paperreferences', using = client)
    cit_s = cit_s.query('terms', PaperReferenceId=paper_ids)
    cit_s = cit_s.params(request_timeout=TIMEOUT)

    # Convert into dictionary format
    for cit_info in cit_s.scan():
        results[cit_info[pr_targets[1]]]['Citations'].append(cit_info[pr_targets[0]])

    # Query for paper fields of study
    fos_s = Search(index = 'paperfieldsofstudy', using = client)
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


def link_paper_info_query(paper_id, cache = True):
    ''' Gets the basic paper information required for the links.
    '''
    # Get citation links
    pr_links = pr_links_query(paper_id)

    # Query results
    link_res = dict()

    # Iterate through the link types
    for link_type, link_papers in pr_links.items():

        # Resulting link results
        link_res[link_type] = list()

        # Iterate through the papers
        for link_paper in link_papers:

            # If cache true
            if cache:
                # Check cache for entries
                link_paper_prop = base_paper_cache_query([link_paper])[0]
            else:
                # Set default to None
                link_paper_prop = None

            # If empty result
            if not link_paper_prop:
                # Do full search
                link_paper_prop = base_paper_db_query(link_paper)

            # Check if query has result
            if link_paper_prop:
                link_res[link_type].append(link_paper_prop)

    # Return results
    return link_res


def paper_info_db_query(paper_id):
    ''' Generate paper info dictionary/json from base databases (not cache).
    '''
    # Query basic properties
    paper_info = base_paper_db_query(paper_id)

    # Check if result is empty
    if not paper_info:
        return None

    # Add citation link information
    paper_info.update(link_paper_info_query(paper_id))

    # Return paper_info
    return paper_info


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
