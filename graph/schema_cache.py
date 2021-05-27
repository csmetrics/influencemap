from elasticsearch import Elasticsearch
from elasticsearch_dsl import DocType, Date, Integer, \
        Float, Long, Text, Keyword, analyzer, Object


class BrowseCache(DocType):
    Type = Keyword(required=True)
    DisplayName = Text(required=True)
    EntityIds = Object(
        required=True,
        properties = {
            "AuthorIds": Long(multi=True),
            "ConferenceIds": Long(multi=True),
            "JournalIds": Long(multi=True),
            "AffiliationIds": Long(multi=True),
            "PaperIds": Long(multi=True)
        }
    )
    Citation = Text(analyzer="standard")
    Year = Integer()
    Field = Text(analyzer="standard")
    Affiliations = Text(analyzer="standard", multi=True)
    Url = Keyword()
    PhotoUrl = Keyword()
    class Meta:
        index = "browse_cache"



# e.g. anu_researchers, fields_medalists, turing_award_winners
class AuthorGroup(DocType):
    # meta.id = hash(Type-NormalizedName)
    Type = Keyword()
    NormalizedNames = Text(multi=True, required = True, analyzer = "standard")
    DisplayName = Text(required = True, analyzer = "standard")
    Year = Integer()
    Affiliations = Text(multi=True, analyzer = "standard")
    Citation = Text(analyzer = "standard")
    Keywords = Text(multi = True, analyzer = "standard")
    CreatedDate = Date(required = True)
    AuthorIDs = Long(multi = True)
    Url = Text()

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
            "AffiliationId": Long()
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
                    "AffiliationId": Long()
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
                    "AffiliationId": Long()
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
