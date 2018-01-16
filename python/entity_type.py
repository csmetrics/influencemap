from enum import Enum

class Entity(Enum):
    AUTH = ('AUTH', {'auth_id': 'authname'}, ['auth_name'], ['auth_count'])
    CFJN = ('CFJN', {'conf_id': 'confname', 'journ_id': 'journname'}, ['conf_name', 'journ_name'], [])
    AFFI = ('AFFI', {'affi_id': 'affiname'}, ['affi_name'], [])
    CONF = ('CONF', {'conf_id': 'confname'}, ['conf_name'], [])
    JOURN = ('JOUR', {'journ_id': 'journname'}, ['journ_name'], [])

    def __init__(self, prefix, edict, key, add):
        self.prefix = prefix
        self.edict = edict
        self.keyn = key
        self.scheme = key + add

# Defines the type of the flower. (Center, Leaves)
class Entity_map:
    def __init__(self, domain, codomain):
        self.domain = domain
        self.codomain = codomain

    def get_map(self):
        return self.domain, self.codomain
