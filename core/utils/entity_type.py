from enum import Enum
from functools import total_ordering


@total_ordering
class Entity_type(Enum):
    ''' Type of entities for the flower
    '''
    AUTH = ('AUTH', 'auth', 'author', 'auth_name', 'Author', 'Author', 'AuthorIDs', 'DisplayAuthorName')
    AFFI = ('AFFI', 'affi', 'institution', 'affi_name', 'Affiliation', 'Affiliation', 'AffiliationIDs', 'Name')
    JOUR = ('JOUR', 'journ', 'journal', 'journ_name', 'Journal', 'Journal', 'JournalID', 'NormalizedShortName')
    FSTD = ('FSTD', 'fos', 'field', 'field_name', 'Field', 'Field', 'FieldOfStudyId', 'NormalizedName')

    def __init__(self, indent, prefix, eid, ename, text, api_type, api_id, api_name):
        self.ident = indent
        self.prefix = prefix
        self.eid = eid
        self.ename = ename
        self.text = text
        self.api_type = api_type
        self.api_id = api_id
        self.api_name = api_name

    def __lt__(self, other):
        return self.ident < other.ident
