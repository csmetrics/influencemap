'''
Functions which combines the different query functions in query_db and
query_cache.

date:   24.06.18
author: Alexander Soen
'''

from core.search.cache_data       import cache_paper_info
from core.search.query_info_cache import paper_info_cache_query
from core.search.query_info_db    import paper_info_multiquery
from core.search.query_utility    import chunker
from itertools import zip_longest


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
