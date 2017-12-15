from enum import Enum, auto

class Entity(Enum):
    AUTH = auto()
    CONF = auto()
    AFFI = cuto()

class Entity_map:
    def __init__(self, domain, codomain):
        self.domain = domain
        self.codomain = codomain

    def get_map(self):
        return domain, codomain

    def get_domain(self):
        return domain

    def get_codomain(self):
        return codomain
