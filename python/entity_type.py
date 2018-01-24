from enum import Enum

# Type of entities for the flower
class Entity_type(Enum):
    AUTH = ('AUTH', 'auth', 'auth_id', 'auth_name')
    AFFI = ('AFFI', 'affi', 'affi_id', 'affi_name')
    CONF = ('CONF', 'conf', 'conf_id', 'conf_abv')
    JOUR = ('JOUR', 'journ', 'journ_id', 'journ_name')

    def __init__(self, indent, prefix, eid, ename):
        self.ident = indent
        self.prefix = prefix
        self.eid = eid
        self.ename = ename

# Defines the type of the flower. (Center, Leaves)
class Entity_map:
    def __init__(self, domain, codomain):
        self.domain = domain
        self.codomain = codomain
        self.ids = [x.eid for x in codomain]
        self.keyn = [x.ename for x in codomain]

    def get_map(self):
        return self.domain, self.codomain

# Class to wrap type and id together
class Entity:
    def __init__(self, entity_id, entity_type):
        self.entity_id = entity_id
        self.entity_type = entity_type
