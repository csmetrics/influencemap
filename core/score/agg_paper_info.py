'''
Aggregates paper information dictionaries into scoring tables/statistics to
display pass to the front-end (Draw flower or display statistics).

date:   26.06.18
author: Alexander Soen
'''

import pandas as pd
from core.utils.entity_type     import Entity_type
from core.score.agg_utils import get_name_mapping, apply_name_mapping

def score_author(paper_info):
    ''' Turns a paper information dictionary into a list of scoring
        dictionaries for authors.
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

                # Influence weight
                weight = 1 / len(reference['Authors']) if reference['Authors'] \
                        else 1

                # Important fields
                row_dict['entity_id']   = ref_author['AuthorName']
                row_dict['influenced']  = 0
                row_dict['influencing'] = weight
                try:
                    row_dict['influence_date'] = paper_info['Year']
                except KeyError:
                    row_dict['influence_date'] = None

                score_list.append(row_dict)

    # Check if citations are empty
    if 'Citations' in paper_info:
        # Iterate through the citations
        for citation in paper_info['Citations']:
            # Go through each of the authors
            for cite_author in citation['Authors']:
                row_dict = dict()

                # Influence weight
                weight = 1 / len(paper_info['Authors']) if \
                         paper_info['Authors'] else 1

                # Important fields
                row_dict['entity_id']   = cite_author['AuthorName']
                row_dict['influenced']  = weight
                row_dict['influencing'] = 0
                try:
                    row_dict['influence_date'] = citation['Year']
                except KeyError:
                    row_dict['influence_date'] = None

                score_list.append(row_dict)

    return score_list


def score_affiliation(paper_info):
    ''' Turns a paper information dictionary into a list of scoring
        dictionary for affiliations.
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

                # Influence weight
                weight = 1 / len(reference['Authors']) if reference['Authors'] \
                         else 1

                # Important fields
                try:
                    row_dict['entity_id']   = ref_author['AffiliationName']
                except KeyError:
                    continue
                row_dict['influenced']  = 0
                row_dict['influencing'] = weight
                try:
                    row_dict['influence_date'] = paper_info['Year']
                except KeyError:
                    row_dict['influence_date'] = None

                score_list.append(row_dict)

    # Check if citations are empty
    if 'Citations' in paper_info:
        # Iterate through the citations
        for citation in paper_info['Citations']:
            # Go through each of the authors
            for cite_author in citation['Authors']:
                row_dict = dict()

                # Influence weight
                weight = 1 / len(paper_info['Authors']) if \
                         paper_info['Authors'] else 1

                # Important fields
                try:
                    row_dict['entity_id']   = cite_author['AffiliationName']
                except KeyError:
                    continue
                row_dict['influenced']  = weight
                row_dict['influencing'] = 0
                try:
                    row_dict['influence_date'] = citation['Year']
                except KeyError:
                    row_dict['influence_date'] = None

                score_list.append(row_dict)

    return score_list


def score_conference(paper_info):
    ''' Turns a paper information dictionary into a list of scoring
        dictionary for conferences.
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
                entity_id = reference['ConferenceInstanceId']
            except KeyError:
                try:
                    entity_id = reference['ConferenceName']
                except KeyError:
                    continue

            # Important fields
            row_dict['entity_id']   = entity_id
            row_dict['influenced']  = 0
            row_dict['influencing'] = 1
            try:
                row_dict['influence_date'] = paper_info['Year']
            except KeyError:
                row_dict['influence_date'] = None

            score_list.append(row_dict)

    # Check if citations are empty
    if 'Citations' in paper_info:
        # Iterate through the citations
        for citation in paper_info['Citations']:
            row_dict = dict()

            # Make entity id
            try:
                entity_id = citation['ConferenceInstanceId']
            except KeyError:
                try:
                    entity_id = citation['ConferenceName']
                except KeyError:
                    continue

            # Important fields
            row_dict['entity_id']   = entity_id
            row_dict['influenced']  = 1
            row_dict['influencing'] = 0
            try:
                row_dict['influence_date'] = citation['Year']
            except KeyError:
                row_dict['influence_date'] = None

            score_list.append(row_dict)

    return score_list


def score_journal(paper_info):
    ''' Turns a paper information dictionary into a list of scoring
        dictionary for journals.
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
                entity_id = reference['JournalName']
            except KeyError:
                continue

            # Important fields
            row_dict['entity_id']   = entity_id
            row_dict['influenced']  = 0
            row_dict['influencing'] = 1
            try:
                row_dict['influence_date'] = paper_info['Year']
            except KeyError:
                row_dict['influence_date'] = None

            score_list.append(row_dict)

    # Check if citations are empty
    if 'Citations' in paper_info:
        # Iterate through the citations
        for citation in paper_info['Citations']:
            row_dict = dict()

            # Make entity id
            try:
                entity_id = citation['JournalName']
            except KeyError:
                continue

            # Important fields
            row_dict['entity_id']   = entity_id
            row_dict['influenced']  = 1
            row_dict['influencing'] = 0
            try:
                row_dict['influence_date'] = citation['Year']
            except KeyError:
                row_dict['influence_date'] = None

            score_list.append(row_dict)

    return score_list


def score_paper_info(paper_info, entity_type):
    ''' Score paper information depending on specific target type.
    '''
    # Call query functions depending on type given
    # Author
    if entity_type == Entity_type.AUTH:
        return score_author(paper_info)

    # Affiliation
    if entity_type == Entity_type.AFFI:
        return score_affiliation(paper_info)

    # Conference
    if entity_type == Entity_type.CONF:
        return score_conference(paper_info)

    # Journal
    if entity_type == Entity_type.JOUR:
        return score_journal(paper_info)

    # Otherwise
    return None


def score_paper_info_list(paper_info_list, leaves):
    ''' Provides a scoring pandas dataframe given a list of paper information
        and leaf configuration of flower to represent the scoring.
    '''
    # Query results
    score_list = list()
    
    # Iterate through different entity types for scoring dictionaries
    for paper_info in paper_info_list:
        for leaf in leaves:
            # Get score
            score = score_paper_info(paper_info, leaf)

            # Check if valid score
            if score:
                score_list += score

    # Score dataframe
    score_df = pd.DataFrame(score_list)

    # Return scoring
    return score_df
