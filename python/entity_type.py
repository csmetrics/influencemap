from enum import Enum
import os

# Type of entities for the flower
class Entity_type(Enum):
    AUTH = ('AUTH', 'auth', 'auth_id', 'auth_name', 'Author', 'Author', 'AuthorIDs', 'DisplayAuthorName')
    AFFI = ('AFFI', 'affi', 'affi_id', 'affi_name', 'Affiliation', 'Affiliation', 'AffiliationIDs', 'Name')
    CONF = ('CONF', 'conf', 'conf_id', 'conf_abv', 'Conference', 'ConferenceSeries', 'ConferenceSeriesID', 'ShortName')
    JOUR = ('JOUR', 'journ', 'journ_id', 'journ_name', 'Journal', 'Journal', 'JournalID', 'NormalizedShortName')

    def __init__(self, indent, prefix, eid, ename, text, api_type, api_id, api_name):
        self.ident = indent
        self.prefix = prefix
        self.eid = eid
        self.ename = ename
        self.text = text
        self.api_type = api_type
        self.api_id = api_id
        self.api_name = api_name

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

# Class to wrap type and id together
class Entity:
    def __init__(self, entity_id, entity_type):
        self.entity_id = entity_id
        self.entity_type = entity_type

    def cache_str(self):
        return os.path.join(self.entity_type.ident, self.entity_id)

    def name_str(self):
        return self.entity_type.ident + '-' + self.entity_id
