from enum import Enum

class Entity(Enum):
    AUTH = (['auth_id', 'auth_count'], 'authname')
    CONF = (['conf_id'], 'confname')
    AFFI = (['affi_id'], 'affiname')

    def __init__(self, fields, nmap):
        self.keyn = fields[0]
        self.scheme = fields
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
