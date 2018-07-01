'''
date:   30.06.18
author: Alexander Soen
'''

import numpy as np

def q_score_paper_info_list(paper_info_list):
    ''' Function which scores a list of paper informations.
        Assumes that the information has been filtered for only relevent papers
        are included for scoring (ie. time ranges for the citations).
    '''
    # Counts
    cites_per_paper = list(map(lambda x: len(x['Citations']), paper_info))

    return np.average(cites_per_paper)


def filter_cite_year_range(paper_info_list, year_range=10):
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
            if paper_year - citation['Year'] <= year_range:
                update_citation.append(citation)

        # Update paper_info
        paper_info['Citations'] = update_citation

    return paper_info_list
