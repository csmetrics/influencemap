from enum import Enum
from functools import total_ordering
from core.config import *
from core.search.mag_user_query import *
import pandas as pd
import os

@ total_ordering
class Entity_type(Enum):
    ''' Type of entities for the flower
    '''
    AUTH = ('AUTH', 'auth', 'author', 'auth_name', 'Author', 'Author', 'AuthorIDs', 'DisplayAuthorName')
    AFFI = ('AFFI', 'affi', 'institution', 'affi_name', 'Affiliation', 'Affiliation', 'AffiliationIDs', 'Name')
    CONF = ('CONF', 'conf', 'conference', 'conf_abv', 'Conference', 'ConferenceSeries', 'ConferenceSeriesIDs', 'ShortName')
    JOUR = ('JOUR', 'journ', 'journal', 'journ_name', 'Journal', 'Journal', 'JournalID', 'NormalizedShortName')

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

# Defines the type of the flower. (Center, Leaves)
class Entity_map:
    def __init__(self, domain, codomain):
        self.domain = domain
        self.codomain = codomain
        self.ids = [x.eid for x in codomain]
        self.keyn = [x.ename for x in codomain]

    def get_map(self):
        return self.domain, self.codomain

    def get_center_prefix(self):
        return self.domain.prefix

    def get_center_text(self):
        return self.domain.text

    def get_leave_text(self):
        texts = [e.text for e in self.codomain]

        if len(texts) > 1:
            text1, textr = texts[0], texts[1:]

            return ' and '.join([', '.join(textr), text1])
        else:
            return texts[0]
