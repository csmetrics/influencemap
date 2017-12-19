from enum import Enum

class Entity(Enum):
    AUTH = (['auth_id'], ['auth_id', 'auth_count'], 'authname')
    CONF = (['conf_id', 'journ_id'], ['conf_id', 'journ_id'], 'confname')
    AFFI = (['affi_id'], ['affi_id'], 'affiname')

    def __init__(self, keyn, scheme, nmap):
        self.keyn = keyn
        self.scheme = scheme
        self.nmap = nmap

    def get_keyn(self):
        return self.keyn

    def get_scheme(self):
        return self.scheme

    def get_nmap(self):
        return self.nmap

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
