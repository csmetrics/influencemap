'''
Utility functions for aggregated tables.

date:   27.06.18
author: Alexander Soen
'''

from core.search.query_name import name_check_query

def get_name_mapping(score_df):
    ''' Creates a name mapping for a score dataframe with both an entity id and
        entity type column
    '''
    # Create name mapping dictionary
    name_mapping = dict()
    for entity_type, entity_df in score_df.groupby('entity_type'):
        entity_names =  list(set(entity_df['entity_name']))

        # Naming dictionary for specific type
        name_map = name_check_query(entity_type, entity_names)
        name_mapping[entity_type] = name_map

    return name_mapping


def apply_name_mapping(row, name_mapping):
    ''' Function to apply the name mapping given by "get_name_mapping".
    '''
    try:
        return name_mapping[row['entity_type']][row['entity_name']]
    except KeyError:
        return None


def is_self_cite(paper_prop, self):
    ''' Determines if a paper property is a self citation depending on a list
        of self names.
    '''
    # If no self names
    if not self:
        return False

    names = list()

    # Get all author names and affiliation names
    if 'Authors' in paper_prop:
        for author in paper_prop['Authors']:
            if 'AuthorName' in author:
                names.append(author['AuthorName'])
            if 'AffiliationName' in author:
                names.append(author['AffiliationName'])

    # Get field of study names
    if 'FieldOfStudy' in paper_prop:
        for fos in paper_prop['FieldOfStudy']:
            if 'FieldOfStudyName' in fos:
                names.append(fos['FieldOfStudyName'])

    # Add other potential fields
    fields = ['ConferenceName', 'JournalName']
    for field in fields:
        if field in paper_prop:
            names.append(paper_prop[field])

    return any(i in self for i in names)


def get_coauthor_mapping(paper_info_list):
    ''' Returns a list of coauthors given paper_infos.
    '''
    coauthors = set()
    for paper_info in paper_info_list:
        # Names in 'Authors' field
        for author in paper_info['Authors']:
            if 'AuthorName' in author:
                coauthors.add(author['AuthorName'])
            if 'AffiliationName' in author:
                coauthors.add(author['AffiliationName'])

        if 'ConferenceName' in paper_info:
            coauthors.add(paper_info['ConferenceName'])
        if 'JournalName' in paper_info:
            coauthors.add(paper_info['JournalName'])

        for fos in paper_info['FieldsOfStudy']:
            if 'FieldOfStudyName' in fos:
                coauthors.add(fos['FieldOfStudyName'])

    return list(coauthors)


def flag_coauthor(score_df, coauthors):
    ''' Flags the coauthors of a dataframe.
    '''
    # Check if coauthor set exists
    if not coauthors:
        return score_df

    # Set flag
    score_df['coauthor'] = score_df.apply(
        lambda x: x['entity_name'] in coauthors, axis = 1)

    return score_df
