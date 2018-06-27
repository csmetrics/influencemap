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
    paper_info_res = list()
    for paper_id in paper_ids:
        # Check cache
        paper_info = paper_info_cache_query(paper_id)

        # If non-empty result return
        if paper_info:
            paper_info_res.append(paper_info)
        else:
            to_process.append(paper_id)

    # Check if items do not exist in cache
    if to_process:
        # Get from API and add to cache
        process_res = paper_info_mag_multiquery(to_process)
        cache_paper_info(process_res)

        paper_info_res += process_res

    return paper_info_res


if __name__ == '__main__':
    # TESTING
    from core.search.query_db_pd import author_name_db_query
    from core.search.query_utility import paper_info_to_cache_json
    from core.score.agg_paper_info import score_paper_info_list
    from core.utils.entity_type import Entity_type

    author_df = author_name_db_query('antony l hosking')

    a_papers = list(author_df['PaperId'])

    paper_info_list = list()
    for paper in a_papers:
        print(paper)
        paper_info = paper_info_check_query(paper)
        if paper_info:
            paper_info_list.append(paper_info)

    print(score_paper_info_list(paper_info_list, [Entity_type.JOUR]))
