'''
Functions which combines the different query functions in query_db and
query_cache.

date:   24.06.18
author: Alexander Soen
'''

from core.search.cache_data       import cache_paper_info
from core.search.query_info_cache import paper_info_cache_query
from core.search.query_info_db    import paper_info_db_query
from core.search.query_info_mag   import paper_info_mag_multiquery

def paper_info_check_query(paper_id):
    ''' Query which checks cache for existence first. Otherwise tries to
        generate paper info from basic tables and adds to cache.
    '''
    # Check cache
    paper_info = paper_info_cache_query(paper_id)

    # If non-empty result return
    if paper_info:
        return paper_info

    # Otherwise check main database
    paper_info = paper_info_db_query(paper_id)

    # If empty result
    if not paper_info:
        return None

    # Otherwise add to cache then return
    cache_paper_info([paper_info])
    return paper_info


def paper_info_mag_check_multiquery(paper_ids):
    ''' Query which checks cache for existence first. Otherwise tries to
        generate paper info from basic tables and adds to cache.
    '''
    to_process     = list()
    to_add_links   = list()
    paper_info_res = list()
    for paper_id in paper_ids:
        # Check cache
        paper_info = paper_info_cache_query(paper_id)

        # If non-empty result return
        if paper_info:
            # If cache entry is partially complete
            if paper_info['cache_type'] == 'partial':
                print(paper_id, paper_info['PaperTitle'], paper_info['cache_type'])
                del paper_info['cache_type']
                to_add_links.append(paper_info)
            else:
                del paper_info['cache_type']
                paper_info_res.append(paper_info)

        else:
            to_process.append(paper_id)

    print("Complete cache entries found:", len(paper_info_res))
    print("Partial cache entries found:", len(to_add_links))
    print("No cache entries found:", len(to_process))
    print("Total ids to query:", len(paper_ids))

    # Check if items do not exist in cache
    if to_process or to_add_links:
        # Get from API and add to cache
        process_res, partial_res = paper_info_mag_multiquery(to_process,
                                       partial_info = to_add_links)

        print("Complete cached:", len(process_res))
        print("Partial cached:", len(partial_res))

        # Cache
        cache_paper_info(process_res)
        cache_paper_info(partial_res, chunk_size=100)
        paper_info_res += process_res

    return paper_info_res
