from elasticsearch import Elasticsearch
from elasticsearch_dsl import DocType, Date, Integer, \
        Float, Long, Text, Keyword, analyzer, Object

# e.g. anu_researchers, fields_medalists, turing_award_winners
class AuthorGroup(DocType):
    Type = Keyword()
    NormalizedName = Text(required = True, analyzer = "standard")
    DisplayName = Text(required = True, analyzer = "standard")
    Year = Integer()
    Affiliation = Text(analyzer = "standard")
    Citation = Text(analyzer = "standard")
    Keywords = Keyword(multi = True)
    CreatedDate = Date(required = True)

    class Meta:
        index = "browse_author_group"


# e.g. conf/journals, univ+field
class PaperGroup(DocType):
    Type = Keyword()
    NormalizedName = Text(required = True, analyzer = "standard")
    DisplayName = Text(required = True, analyzer = "standard")
    Year = Integer()
    PaperIds = Long(multi = True)
    Field = Text(analyzer = "standard")
    Keywords = Keyword(multi = True)
    CreatedDate = Date(required = True)

    class Meta:
        index = "browse_paper_group"
