'''
Aggregates paper information dictionaries into scoring tables/statistics to
display pass to the front-end (Draw flower or display statistics).

date:   25.06.18
author: Alexander Soen
'''

import pandas as pd
from core.utils.entity_type import Entity_type

def score_author(paper_info):
    ''' Turns a paper information dictionary into a list of scoring
        pandas table for authors.
    '''
    # Score results
    score_list = list()

    # Check if references are empty
    if 'References' in paper_info:
        # Iterate through the references
        for reference in paper_info['References']:
            # Go through each of the authors
            for ref_author in reference['Authors']:
                row_dict = dict()

                # Make entity id
                try:
                    entity_id = (Entity_type.AUTH, ref_author['AuthorId'])
                except KeyError:
                    continue

                # Important fields
                row_dict['entity_id']      = entity_id
                row_dict['influenced']     = 1 / len(reference['Authors'])
                row_dict['influencing']    = 0
                row_dict['influence_date'] = paper_info['Year']

                score_list.append(row_dict)

    # Check if citations are empty
    if 'Citations' in paper_info:
        # Iterate through the citations
        for citation in paper_info['Citations']:
            # Go through each of the authors
            for cite_author in citation['Authors']:
                row_dict = dict()

                # Make entity id
                try:
                    entity_id = (Entity_type.AUTH, cite_author['AuthorId'])
                except KeyError:
                    continue

                # Important fields
                row_dict['entity_id']      = entity_id
                row_dict['influenced']     = 0
                row_dict['influencing']    = 1 / len(paper_info['Authors'])
                row_dict['influence_date'] = citation['Year']

                score_list.append(row_dict)

    return pd.DataFrame(score_list)


def score_affiliation(paper_info):
    ''' Turns a paper information dictionary into a list of scoring
        pandas table for affiliations.
    '''
    # Score results
    score_list = list()

    # Check if references are empty
    if 'References' in paper_info:
        # Iterate through the references
        for reference in paper_info['References']:
            # Go through each of the authors
            for ref_author in reference['Authors']:
                row_dict = dict()

                # Make entity id
                try:
                    entity_id = (Entity_type.AFFI, ref_author['AffiliationId'])
                except KeyError:
                    continue

                # Important fields
                row_dict['entity_id']      = entity_id
                row_dict['influenced']     = 1 / len(reference['Authors'])
                row_dict['influencing']    = 0
                row_dict['influence_date'] = paper_info['Year']

                score_list.append(row_dict)

    # Check if citations are empty
    if 'Citations' in paper_info:
        # Iterate through the citations
        for citation in paper_info['Citations']:
            # Go through each of the authors
            for cite_author in citation['Authors']:
                row_dict = dict()

                # Make entity id
                try:
                    entity_id = (Entity_type.AFFI, cite_author['AffiliationId'])
                except KeyError:
                    continue

                # Important fields
                row_dict['entity_id']      = entity_id
                row_dict['influenced']     = 0
                row_dict['influencing']    = 1 / len(paper_info['Authors'])
                row_dict['influence_date'] = citation['Year']

                score_list.append(row_dict)

    return pd.DataFrame(score_list)


def score_conference(paper_info):
    ''' Turns a paper information dictionary into a list of scoring
        pandas table for conferences.
    '''
    # Score results
    score_list = list()

    # Check if references are empty
    if 'References' in paper_info:
        # Iterate through the references
        for reference in paper_info['References']:
            row_dict = dict()

            # Make entity id
            try:
                entity_id = (Entity_type.CONF,
                             reference['ConferenceInstanceId'])
            except KeyError:
                continue

            # Important fields
            row_dict['entity_id']      = entity_id
            row_dict['influenced']     = 1
            row_dict['influencing']    = 0
            row_dict['influence_date'] = paper_info['Year']

            score_list.append(row_dict)

    # Check if citations are empty
    if 'Citations' in paper_info:
        # Iterate through the citations
        for citation in paper_info['Citations']:
            row_dict = dict()

            # Make entity id
            try:
                entity_id = (Entity_type.CONF, citation['ConferenceInstanceId'])
            except KeyError:
                continue

            # Important fields
            row_dict['entity_id']      = entity_id
            row_dict['influenced']     = 0
            row_dict['influencing']    = 1
            row_dict['influence_date'] = citation['Year']

            score_list.append(row_dict)

    return pd.DataFrame(score_list)


def score_journal(paper_info):
    ''' Turns a paper information dictionary into a list of scoring
        pandas table for journals.
    '''
    # Score results
    score_list = list()

    # Check if references are empty
    if 'References' in paper_info:
        # Iterate through the references
        for reference in paper_info['References']:
            row_dict = dict()

            # Make entity id
            try:
                entity_id = (Entity_type.JOUR, reference['JournalId'])
            except KeyError:
                continue

            # Important fields
            row_dict['entity_id']      = entity_id
            row_dict['influenced']     = 1
            row_dict['influencing']    = 0
            row_dict['influence_date'] = paper_info['Year']

            score_list.append(row_dict)

    # Check if citations are empty
    if 'Citations' in paper_info:
        # Iterate through the citations
        for citation in paper_info['Citations']:
            row_dict = dict()

            # Make entity id
            try:
                entity_id = (Entity_type.JOUR, citation['JournalId'])
            except KeyError:
                continue

            # Important fields
            row_dict['entity_id']      = entity_id
            row_dict['influenced']     = 0
            row_dict['influencing']    = 1
            row_dict['influence_date'] = citation['Year']

            score_list.append(row_dict)

    return pd.DataFrame(score_list)
