# This file is no longer supported as it has been deprecated
# due to the transition from Microsoft Academic Graph to OpenAlex for our dataset.
# 2023 Jun 29 Minjeong Shin (minjeong.shin@anu.edu.au)


import re
from elasticsearch import Elasticsearch, RequestsHttpConnection
from elasticsearch_dsl import Search
from graph.config import conf

client = Elasticsearch(
    conf.get("elasticsearch.hostname"),
    timeout=30,
    connection_class=RequestsHttpConnection,
    http_compress=True)


def query_names_with_matches(index, fields_list, search_phrase, max_return=30):
    result = []
    matches = [{"match": {field: search_phrase}} for field in fields_list]

    # the script field nested within functions defines the formula used to order the retrieved documents
    # log citation count is included to ensure that large entities with slightly different names are not missed
    # the addition of 10 is to account for relevant entities with 0, 1 or otherwise few citations
    # The _score is taken to a higher power to increase its significance

    q = {
      "size": max_return,
      "from": 0,
      "query":{
          "function_score": {
            "query": {
              "bool":{
                "should": matches
              }
            },
            "functions": [
              {"script_score": {
                "script": "Math.pow(_score, 3) * (Math.log((doc['CitationCount'].value + 10)))"
              }}
            ]
          }
        }
      }

    s = Search(using=client, index=index).params(preserve_order=True)
    s.update_from_dict(q)

    count = 0
    for res in s.scan():
        if count >= max_return:
            break
        result.append(res.to_dict())
        count += 1
    return result


def query_names_with_exact_matches(index, field, search_phrase, max_return=30):
    result = []
    normalized_search_phrase = re.sub(r'\W+', ' ', search_phrase).lower()
    # to reduce the search time, we only allow exact string match

    q = {
      "size": max_return,
      "sort": [
        { "CitationCount" : "desc" }
      ],
      "query":{
          "match": {
            field: {
              "query": normalized_search_phrase,
              "operator": "and"
            }
          }
        }
      }
    s = Search(using=client, index=index).params(preserve_order=True)
    s.update_from_dict(q)

    count = 0
    for res in s.scan():
        if count >= max_return:
            break
        result.append(res.to_dict())
        count += 1
    return result


def query_conference_series(search_phrase):
    return query_names_with_matches(conf.get('index.conf_s'), ["DisplayName","NormalizedName"] , search_phrase)

def query_journal(search_phrase):
    return query_names_with_matches(conf.get('index.journal'), ["DisplayName", "NormalizedName"], search_phrase)

def query_affiliation(search_phrase):
    return query_names_with_matches(conf.get('index.aff'), ["DisplayName", "NormalizedName"], search_phrase)

def query_paper(search_phrase):
    # papers = query_names_with_matches("papers", ["PaperTitle", "OriginalTitle", "BookTitle"], search_phrase)
    papers = query_names_with_exact_matches(conf.get('index.paper'), "PaperTitle", search_phrase)
    for paper in papers:
        author_ids = get_authors_from_paper(paper["PaperId"])
        paper["Authors"] = get_display_names_from_author_ids(author_ids)
    return papers

def query_author(search_phrase):
    # authors = query_names_with_matches("authors", ["DisplayName", "NormalizedName"], search_phrase)
    authors = query_names_with_exact_matches(conf.get('index.author'), "NormalizedName", search_phrase)
    for author in authors:
        if "LastKnownAffiliationId" in author:
            author["Affiliation"] = get_names_from_affiliation_ids([author["LastKnownAffiliationId"]])[0]
            print(author["Affiliation"])
    return authors

def query_topic(search_phrase):
    topics = query_names_with_matches(conf.get('index.fos'), ["DisplayName", "NormalizedName"], search_phrase)
    return [t for t in topics if t["Level"] < 2] # only returns level 0 or 1 topics


def query_entity(entityType, keyword):
    data = []
    if "conference" in entityType:
        data += [(val, "conference") for val in query_conference_series(keyword)]
    if "journal" in entityType:
        data += [(val, "journal") for val in query_journal(keyword)]
    if "institution" in entityType:
        data += [(val, "institution") for val in query_affiliation(keyword)]
    if "paper" in entityType:
        data += [(val, "paper") for val in query_paper(keyword)]
    if "author" in entityType:
        data += [(val, "author") for val in query_author(keyword)]
    if "topic" in entityType:
        data += [(val, "topic") for val in query_topic(keyword)]
    return data


def get_authors_from_paper(paper_id):
    result = []
    q = {
      "_source": "AuthorId",
      "size": 3,
      "sort": [{"AuthorSequenceNumber":"asc"}],
      "query": {
        "term": {"PaperId": paper_id}
      }
    }
    s = Search(using=client, index=conf.get('index.paa'))
    s.update_from_dict(q)
    response = s.execute()
    data = response.to_dict()["hits"]["hits"]
    author_ids = [res["_source"]["AuthorId"] for res in data]
    return author_ids


def get_names_from_entity(entity_ids, index, id_field, name_field, with_id=False):

    result = []
    q = {
      "_source": [name_field,id_field],
      "size": 100,
      "query": {
        "terms": {id_field : entity_ids}
      }
    }
    s = Search(using=client, index=index)
    s.update_from_dict(q)
    response = s.execute()
    data = response.to_dict()["hits"]["hits"]
    id_name_dict = {res["_source"][id_field]: res["_source"][name_field] for res in data}
    if with_id:
        return id_name_dict
    ids = [id_name_dict[eid] for eid in entity_ids]

    return ids


def get_names_from_conference_ids(entity_ids):
    return get_names_from_entity(entity_ids, conf.get('index.conf_s'), "ConferenceSeriesId", "NormalizedName")

def get_names_from_affiliation_ids(entity_ids, with_id=False):
    return get_names_from_entity(entity_ids, conf.get('index.aff'), "AffiliationId", "DisplayName", with_id=with_id)

def get_names_from_journal_ids(entity_ids):
    return get_names_from_entity(entity_ids, conf.get('index.journal'), "JournalId", "NormalizedName")

def get_display_names_from_conference_ids(entity_ids):
    return get_names_from_entity(entity_ids, conf.get('index.conf_s'), "ConferenceSeriesId", "DisplayName", with_id=True)

def get_display_names_from_journal_ids(entity_ids):
    return get_names_from_entity(entity_ids, conf.get('index.journal'), "JournalId", "DisplayName", with_id=True)

def get_display_names_from_author_ids(entity_ids, with_id=False):
    return get_names_from_entity(entity_ids, conf.get('index.author'), "AuthorId", "DisplayName", with_id=with_id)

def get_display_names_from_fos_ids(entity_ids, with_id=False):
    return get_names_from_entity(entity_ids, conf.get('index.fos'), "FieldOfStudyId", "DisplayName", with_id=with_id)



def author_order_query(paper_id):
    ''' Find author name from id.
    '''
    # Query for paa
    authors_s = Search(index = 'paperauthoraffiliations', using = client)
    authors_s = authors_s.query('term', PaperId=paper_id)
    authors_s = authors_s.source(['AuthorId', 'AuthorSequenceNumber'])
    authors_s = authors_s.params(request_timeout=30)

    order = dict()
    for authors in authors_s.scan():
        # Add to order dictionary
        order[authors['AuthorId']] = authors['AuthorSequenceNumber']

    return order
