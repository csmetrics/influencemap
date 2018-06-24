'''
Functions which combines the different query functions in query_db and
query_cache.

date:   24.06.18
author: Alexander Soen
'''

from core.search.cache_data  import cache_paper_info
from core.search.query_cache import paper_info_cache_query
from core.search.query_db    import paper_info_db_query

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
    cache_paper_info(paper_info)
    return paper_info


if __name__ == '__main__':
    # TESTING
    from core.search.query_db_pd import author_name_db_query
    from elasticsearch import helpers
    from core.search.query_utility import paper_info_to_cache_json

    author_df = author_name_db_query('antony l hosking')

    a_papers = list(author_df['PaperId'])
    cache_json = list()

    for paper in a_papers:
        print(paper_info_check_query(paper))

    print(paper_info_check_query(paper+1))
