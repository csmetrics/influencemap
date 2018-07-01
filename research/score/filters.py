'''
Filter functions.

date:   30.06.18
author: Alexander Soen
'''

def filter_pub_year_diff(paper_info_list, diff=10):
    ''' Filter the citations for paper information depending on the year of
        citation publication.
    '''
    for paper_info in paper_info_list:
        # If no year data skip
        paper_year = paper_info['Year']
        if not paper_year:
            continue

        update_citation = list()

        for citation in paper_info['Citations']:
            # Check for empty year value
            if not citation['Year']:
                continue

            # Check if in year range
            if paper_year - citation['Year'] <= diff:
                update_citation.append(citation)

        # Update paper_info
        paper_info['Citations'] = update_citation

    return paper_info_list


def filter_year_range(paper_info_list, bot_year, top_year):
    ''' Filter paper information depending on year range.
    '''
    return_list = list()
    for paper_info in paper_info_list:
        # Check for empty year value
        if not paper_info['Year']:
            continue

        # Check if it is in year range
        if paper_info['Year'] >= bot_year and paper_info['Year'] <= top_year:
            return_list.append_paper_info

    return return_list
