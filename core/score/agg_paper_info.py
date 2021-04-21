'''
Aggregates paper information dictionaries into scoring tables/statistics to
display pass to the front-end (Draw flower or display statistics).

date:   29.06.18
author: Alexander Soen
'''

import pandas as pd
from core.utils.entity_type import Entity_type
from core.score.agg_utils   import is_self_cite


def to_influence_dict(name, infed, infing):
    '''
    '''
    return {
            'entity_name': name,
            'influenced' : infed,
            'influencing': infing
            }


def score_paper_info(paper_info, self=list()):
    '''
    '''
    # Score results
    score_list = {
            'CONF': list(),
            'JOUR': list(),
            'AFFI': list(),
            'AUTH': list(),
            'FSTD': list(),
            }

    ###  COAUTHOR DUMMY VALUES ###
    coauthor_const = {
        'self_cite': False,
        'coauthor': True,
        'publication_year': paper_info['Year'] if 'Year' in paper_info else None,
        'influence_year': paper_info['Year'] if 'Year' in paper_info else None,
        'ego_paper_id': int(paper_info['PaperId']),
        'link_paper_id': int(paper_info['PaperId'])
    }

    make_dummy = lambda x: dict(**to_influence_dict(x, 0, 0), **coauthor_const)

    # Get venue value
    if 'ConferenceName' in paper_info:
        score_list['CONF'].append(make_dummy(paper_info['ConferenceName']))
    if 'JournalName' in paper_info:
        score_list['JOUR'].append(make_dummy(paper_info['JournalName']))

    # Get author combinations
    for paa in paper_info['Authors']:
        if 'AuthorName' in paa:
            score_list['AUTH'].append(make_dummy(paa['AuthorName']))
        if 'AffiliationName' in paa:
            score_list['AFFI'].append(make_dummy(paa['AffiliationName']))

    # Get fos fields
    try:
        for pfos in paper_info['FieldsOfStudy']:
            if 'FieldOfStudyName' in pfos and pfos['FieldOfStudyLevel'] == 1:
                score_list['FSTD'].append(make_dummy(pfos['FieldOfStudyName']))
    except:
        print(paper_info['PaperId'])
    ###  COAUTHOR DUMMY VALUES ###

    ###  REFERENCE VALUES ###
    # Calculate references influence
    for reference in paper_info['References']:
        # Check if it is a self citation
        ref_const = {
            'self_cite': is_self_cite(reference, self),
            'coauthor': False,
            'publication_year': reference['Year'] if 'Year' in paper_info else None,
            'influence_year': paper_info['Year'] if 'Year' in paper_info else None,
            'ego_paper_id': int(paper_info['PaperId']),
            'link_paper_id': int(reference['PaperId'])
        }

        make_score = lambda x: dict(**to_influence_dict(*x), **ref_const)

        # Get venue value
        if 'ConferenceName' in reference:
            score_list['CONF'].append(make_score((reference['ConferenceName'], 0, 1)))
        if 'JournalName' in reference:
            score_list['JOUR'].append(make_score((reference['JournalName'], 0, 1)))

        # Get author combinations
        influencing_paa = 1 / len(reference['Authors'])
        for paa in reference['Authors']:
            if 'AuthorName' in paa:
                score_list['AUTH'].append(make_score((paa['AuthorName'], 0, influencing_paa)))
            if 'AffiliationName' in paa:
                score_list['AFFI'].append(make_score((paa['AffiliationName'], 0, influencing_paa)))

        # Get fos fields
        try:
            for pfos in reference['FieldsOfStudy']:
                if 'FieldOfStudyName' in pfos and pfos['FieldOfStudyLevel'] == 1:
                    score_list['FSTD'].append(make_score((pfos['FieldOfStudyName'], 0, 1)))
        except:
            print(paper_info['PaperId'], reference['PaperId'])
    ###  REFERENCE VALUES ###


    ###  CITATION VALUES ###

    # Calculate the influenced score for paa (for this paper)
    influenced_paa = 1 / len(paper_info['Authors']) if 'Authors' in paper_info else 1

    # Calculate citation influence (influenced)
    for citation in paper_info['Citations']:
        # Check if it is a self citation
        cit_const = {
            'self_cite': is_self_cite(citation, self),
            'coauthor': False,
            'publication_year': paper_info['Year'] if 'Year' in paper_info else None,
            'influence_year': citation['Year'] if 'Year' in paper_info else None,
            'ego_paper_id': int(paper_info['PaperId']),
            'link_paper_id': int(citation['PaperId'])
        }

        make_score = lambda x: dict(**to_influence_dict(*x), **cit_const)

        # Get venue value
        if 'ConferenceName' in citation:
            score_list['CONF'].append(make_score((citation['ConferenceName'], 1, 0)))
        if 'JournalName' in citation:
            score_list['JOUR'].append(make_score((citation['JournalName'], 1, 0)))

        # Get author combinations
        influencing_paa = 1 / len(citation['Authors'])
        for paa in citation['Authors']:
            if 'AuthorName' in paa:
                score_list['AUTH'].append(make_score((paa['AuthorName'], influenced_paa, 0)))
            if 'AffiliationName' in paa:
                score_list['AFFI'].append(make_score((paa['AffiliationName'], influenced_paa, 0)))

        # Get fos fields
        for pfos in citation['FieldsOfStudy']:
            if 'FieldOfStudyName' in pfos and pfos['FieldOfStudyLevel'] == 1:
                score_list['FSTD'].append(make_score((pfos['FieldOfStudyName'], 1, 0)))
    ###  CITATION VALUES ###

    return score_list


def score_paper_info_list(paper_info_list, self=list()):
    '''
    '''
    # Query results
    score_list = {
            'CONF': list(),
            'JOUR': list(),
            'AFFI': list(),
            'AUTH': list(),
            'FSTD': list(),
            }

    # Turn paper information into score dictionary
    for paper_info in paper_info_list:
        single_score = score_paper_info(paper_info, self)
        for k, v in single_score.items():
            score_list[k] += v

    # Score dataframe
    return score_list


DF_COLUMNS = [
        'entity_name',
        'entity_type',
        'influence_year',
        'publication_year',
        'self_cite',
        'coauthor',
        'influenced',
        'influencing',
        'ego_paper_id',
        'link_paper_id'
        ]


def score_leaves(score_list, leaves):
    '''
    '''
    dfs = []
    for leaf in leaves:
        if score_list[leaf.ident]:
            dfs.append(pd.DataFrame(score_list[leaf.ident], columns=DF_COLUMNS))

    score_df = (
        pd.concat(dfs, ignore_index=True)
        if dfs
        else pd.DataFrame(columns=DF_COLUMNS))

    score_df['self_cite'] = score_df['self_cite'].astype('bool')
    score_df['coauthor'] = score_df['coauthor'].astype('bool')

    return score_df
