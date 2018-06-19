from elasticsearch import Elasticsearch
from elasticsearch_dsl import DocType, Date, Integer, \
        Float, Long, Text, Keyword, analyzer, Object

# e.g. anu_researchers, fields_medalists, turing_award_winners
class AuthorGroup(DocType):
    # meta.id = hash(Type-NormalizedName)
    Type = Keyword()
    NormalizedName = Text(required = True, analyzer = "standard")
    DisplayName = Text(required = True, analyzer = "standard")
    Year = Integer()
    Affiliation = Text(analyzer = "standard")
    Citation = Text(analyzer = "standard")
    Keywords = Text(multi = True, analyzer = "standard")
    CreatedDate = Date(required = True)

    class Meta:
        index = "browse_author_group"


# e.g. conf/journals, univ+field
class PaperGroup(DocType):
    # meta.id = hash(Year-Field-NormalizedName)
    Type = Keyword()
    NormalizedName = Text(required = True, analyzer = "standard")
    DisplayName = Text(required = True, analyzer = "standard")
    Year = Integer()
    PaperIds = Long(multi = True)
    Field = Text(analyzer = "standard")
    Keywords = Text(multi = True, analyzer = "standard")
    CreatedDate = Date(required = True)

    class Meta:
        index = "browse_paper_group"


# general Author information cache
class AuthorInfo(DocType):
    # meta.id = hash(NormalizedName)
    NormalizedName = Text(required = True, analyzer = "standard")
    DisplayName = Text(required = True, analyzer = "standard")
    AuthorIds = Long(multi = True)
    Papers = Object(
        multi = True,
        properties = {
            "AuthorId": Long(required = True),
            "PaperIds": Long(multi = True)
        }
    )
    CreatedDate = Date(required = True)

    class Meta:
        index = "author_info"

# general Paper information cache
class PaperInfo(DocType):
    # meta.id = PaperId
    PaperId = Long(required = True)
    Authors = Object(
        multi = True,
        properties = {
            "AuthorId": Long(required = True),
            "AffiliationId": Long(required = True)
        }
    )
    ConferenceId = Long()
    JournalId = Long()
    Year = Integer()
    References = Object(
        multi = True,
        properties = {
            "PaperId": Long(required = True),
            "Authors": Object(
                multi = True,
                properties = {
                    "AuthorId": Long(required = True),
                    "AffiliationId": Long(required = True)
                }
            ),
            "ConferenceId": Long(),
            "JournalId": Long(),
            "Year": Integer()
        }
    )
    Citations = Object(
        multi = True,
        properties = {
            "PaperId": Long(required = True),
            "Authors": Object(
                multi = True,
                properties = {
                    "AuthorId": Long(required = True),
                    "AffiliationId": Long(required = True)
                }
            ),
            "ConferenceId": Long(),
            "JournalId": Long(),
            "Year": Integer()
        }
    )
    CreatedDate = Date(required = True)

    class Meta:
        index = "paper_info"
