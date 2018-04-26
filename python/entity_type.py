from enum import Enum
from mag_interface import *
import os

# Type of entities for the flower
class Entity_type(Enum):
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

from mag_user_query import *

# Class to wrap type and id together
class Entity:
    def __init__(self, entity_name, entity_id, entity_type):
        self.entity_name = entity_name
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.display_info = None
        self.paper_df = None

    def cache_str(self):
        return os.path.join(self.entity_type.ident, str(self.entity_id))

    def name_str(self):
        return self.entity_type.ident + '-' + self.entity_id

    def get_papers(self):
        """
        """
        if self.paper_df is not None:
            return self.paper_df

        cache_path = os.path.join(CACHE_PAPERS_DIR, self.cache_str())
        try:
            self.paper_df = pd.read_pickle(cache_path)
        except FileNotFoundError:
            self.paper_df = ent_paper_df(self)

            if self.paper_df is not None:
                # Cache 
                self.paper_df.to_pickle(cache_path)
                os.chmod(cache_path, 0o777)

        return self.paper_df
