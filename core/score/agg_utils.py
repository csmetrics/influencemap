'''
Utility functions for aggregated tables.

date:   27.06.18
author: Alexander Soen
'''

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
