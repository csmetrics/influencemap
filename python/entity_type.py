from enum import Enum

class Entity(Enum):
    AUTH = ('AUTH', ['auth_id'], ['auth_name'])
    CFJN = ('CFJN', ['conf_id', 'journ_id'], ['conf_abv', 'journ_name'])
    AFFI = ('AFFI', ['affi_id'], ['affi_name'])
    CONF = ('CONF', ['conf_id'], ['conf_abv'])
    JOURN = ('JOUR', ['journ_id'], ['journ_name'])

    def __init__(self, prefix, ids, key):
        self.prefix = prefix
        self.ids = ids
        self.keyn = key

# Defines the type of the flower. (Center, Leaves)
class Entity_map:
    def __init__(self, domain, codomain):
        self.domain = domain
        self.codomain = codomain

    def get_map(self):
        return self.domain, self.codomain
