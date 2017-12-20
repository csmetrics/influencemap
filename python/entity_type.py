from enum import Enum

class Entity(Enum):
    AUTH = ({'auth_id': 'authname'}, ['auth_id'], ['auth_count'])
    CFJN = ({'conf_id': 'confname', 'journ_id': 'journname'}, ['conf_id', 'journ_id'], [])
    AFFI = ({'affi_id': 'affiname'}, ['affi_id'], [])
    CONF = ({'conf_id': 'confname'}, ['conf_id'], [])
    JOURN = ({'journ_id': 'journname'}, ['journ_id'], [])


    def __init__(self, edict, key, add):
        self.edict = edict
        self.keyn = key
        self.scheme = key + add

class Entity_map:
    def __init__(self, domain, codomain):
        self.domain = domain
        self.codomain = codomain

    def get_map(self):
        return self.domain, self.codomain

    def get_domain(self):
        return self.domain

    def get_codomain(self):
        return self.codomain
