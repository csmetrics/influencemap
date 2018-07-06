'''
Scoring functions.

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
    cites_per_paper = list(map(lambda x: len(x['Citations']), paper_info_list))

    return np.average(cites_per_paper)


def n_score_paper_info_list(paper_info_list):
    ''' Generates the n score (number of papers) for paper information.
    '''
    return len(paper_info_list)
