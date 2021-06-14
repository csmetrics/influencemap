import re
from elasticsearch import Elasticsearch, RequestsHttpConnection
from elasticsearch_dsl import Search
from graph.config import conf

client = Elasticsearch(
    conf.get("elasticsearch.hostname"),
    timeout=30,
    connection_class=RequestsHttpConnection,
    http_compress=True)

def query_cache_paper_info(author_id):
    result = {}
    cache_index = "paper_info"
    author_ids = author_id if type(author_id)==list else [author_id]
    q = {"_source": "PaperId",
        "size": 10000,
        "query": {"terms": { "Authors.AuthorId": author_ids}}}
    s = Search(using=client, index=cache_index)
    s.update_from_dict(q)
    response = s.execute()
    data = response.to_dict()["hits"]["hits"]
    # print(data["hits"]["total"])
    paper_ids = [e["_source"]["PaperId"] for e in data]
    return paper_ids

def query_author_group(author_name):
    result = {}
    cache_index = "browse_author_group"
    q = {"_source": "AuthorIds",
        "query": {"match": {"NormalizedNames": author_name}}}
    s = Search(using=client, index=cache_index)
    s.update_from_dict(q)
    response = s.execute()
    data = response.to_dict()["hits"]["hits"]
    author_ids = data[0]["_source"]["AuthorIds"]
    return query_cache_paper_info(author_ids)

def query_browse_group(document_id):
    result = {}
    cache_index = "browse_cache"
    q = {"query": {"match": {"_id": document_id}}}
    s = Search(using=client, index=cache_index)
    s.update_from_dict(q)
    response = s.execute()
    data = response.to_dict()["hits"]["hits"]
    document = data[0]["_source"]
    return document

def search_cache(cache_index, cache_type):
    s = Search(using=client, index=cache_index).query("match", Type=cache_type)
    response = []
    for res in s.scan():
        res_id = res.meta.id
        res = res.to_dict()
        res["_id"] = res_id
        response.append(res)
    return response

def query_paper_group(document_id):
    result = {}
    cache_index = "browse_paper_group"
    q = {"_source": "PaperIds",
        "query": {"match": {"_id": document_id}}}
    s = Search(using=client, index=cache_index)
    s.update_from_dict(q)
    response = s.execute()
    data = response.to_dict()["hits"]["hits"]
    paper_ids = data[0]["_source"]["PaperIds"]
    return paper_ids


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
    return query_names_with_matches("conferenceseries", ["DisplayName","NormalizedName"] , search_phrase)

def query_journal(search_phrase):
    return query_names_with_matches("journals", ["DisplayName", "NormalizedName"], search_phrase)

def query_affiliation(search_phrase):
    return query_names_with_matches("affiliations", ["DisplayName", "NormalizedName"], search_phrase)

def query_paper(search_phrase):
    # papers = query_names_with_matches("papers", ["PaperTitle", "OriginalTitle", "BookTitle"], search_phrase)
    papers = query_names_with_exact_matches("papers", "PaperTitle", search_phrase)
    for paper in papers:
        author_ids = get_authors_from_paper(paper["PaperId"])
        paper["Authors"] = get_display_names_from_author_ids(author_ids)
    return papers

def query_author(search_phrase):
    # authors = query_names_with_matches("authors", ["DisplayName", "NormalizedName"], search_phrase)
    authors = query_names_with_exact_matches("authors", "NormalizedName", search_phrase)
    for author in authors:
        if "LastKnownAffiliationId" in author:
            author["Affiliation"] = get_names_from_affiliation_ids([author["LastKnownAffiliationId"]])[0]
            print(author["Affiliation"])
    return authors


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
    s = Search(using=client, index="paperauthoraffiliations")
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
    return get_names_from_entity(entity_ids, "conferenceseries", "ConferenceSeriesId", "NormalizedName")

def get_names_from_affiliation_ids(entity_ids):
    return get_names_from_entity(entity_ids, "affiliations", "AffiliationId", "DisplayName")

def get_names_from_journal_ids(entity_ids):
    return get_names_from_entity(entity_ids, "journals", "JournalId", "NormalizedName")

def get_display_names_from_conference_ids(entity_ids):
    return get_names_from_entity(entity_ids, "conferenceseries", "ConferenceSeriesId", "DisplayName", with_id=True)

def get_display_names_from_journal_ids(entity_ids):
    return get_names_from_entity(entity_ids, "journals", "JournalId", "DisplayName", with_id=True)

def get_display_names_from_author_ids(entity_ids):
    return get_names_from_entity(entity_ids, "authors", "AuthorId", "DisplayName", with_id=False)

def get_all_browse_cache():
    cache_index = "browse_cache"
    q = {"size": 10000,
        "query": {
          "bool":{
            "must_not":{
              "term": {"Type": "user_generated"}
    }}}}
    s = Search(using=client, index=cache_index)
    s.update_from_dict(q)
    response = s.execute()
    data = response.to_dict()["hits"]["hits"]
    result = [{**e["_source"],"document_id": e["_id"]} for e in data]
    return result

def get_cache_types():
    q = {
      "_source": ["Type"],
      "size": 10000,
      "query": {
        "match_all": {}
      }
    }
    s = Search(using = client, index="browse_cache")
    s.update_from_dict(q)
    response = s.execute()
    data = response.to_dict()["hits"]["hits"]
    result = sorted(list(set(hit["_source"]["Type"]  for hit in data)))
    return result

def check_browse_record_exists(cachetype, displayname):
    cache_index = "browse_cache"
    q = {
      "query" : {
        "constant_score" : {
          "filter" : {
            "bool" : {
              "must" : [
                { "term" : {"Type" : cachetype}},
                { "match" : {"DisplayName" : displayname}}
              ]
            }
          }
        }
      }
    }
    s = Search(using=client, index=cache_index)
    s.update_from_dict(q)
    response = s.execute()
    print(response)
    print(response["hits"])
    print(response["hits"]["hits"])
    names = [hit["_source"]["DisplayName"] for hit in response["hits"]["hits"]]
    return (response["hits"]["total"] > 0, names)


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
