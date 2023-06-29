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