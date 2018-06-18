### How to import graph data to Elasticsearch

1) install prerequisites

```
pip install -r requirements.txt
```

2) pre-process raw files

Use `csplit` to split the huge file into small files.
`csplit` command splits a file into sections determined by context lines. Output pieces of FILE separated to files 'xx00', 'xx01', ..., and output byte counts of each piece to standard output.

usage: `csplit -k filename numlines {repeat}`

*-k* option forces csplit to not remove output files in case of error.

```
### need raw files under {filedir}/Papers/
mkdir Papers
cd Papers
csplit -k ../Papers.txt 1000000 {500}
```


3) run import_graph.ph

```
nohup python import_grapy.py Authors > log_authors &
```

- Note1: # of threads == 4 by default.
- Note2: if the total number of threads exceeds 20, the thread may be killed due to a request timeout error.

### How to Query Elasticsearch
Elasticsearch provides a JSON-style domain-specific language that you can use to execute queries. There are two basic ways to run searches: one is by sending search parameters through the REST request URI and the other by sending them through the REST request body. Please [read the document](https://www.elastic.co/guide/en/elasticsearch/reference/current/_the_search_api.html) before you try to execute queries to Elasticsearch.

The [Dev Tools page in Kibana](http://130.56.248.105:5601/app/kibana#/dev_tools/) contains development tools that you can use to interact with your data. Elasticsearch only returns 10 documents by default. You can change this using `"size": {number}` or [Scroll API](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-request-scroll.html).

#### Example code snippets to try

- List all the indices
```
GET _cat/indices?v
```

- Get *papers* index properties
```
GET papers/_mapping
```

- Search matching *authors* with confidence score.
```
  GET authors/_search
  {
    "_source":["_score", "NormalizedName", "AuthorId", "PaperCount"],
    "query": {
      "match" : {
        "DisplayName" : "Stephen Blackburn"
      }
    }
  }
```

- Get *(AuthorId, NormalizedName, PaperCount)* if the *PaperCount* is greater than 500.
```
  GET authors/_search
  {
    "_source": ["AuthorId", "NormalizedName", "PaperCount"],
    "size": 10000,
    "query": {
      "range" : {
        "PaperCount" : {
          "gte" : 500
        }
      }
    }
  }
```

- Get all the *(paperId, AffiliationId)* from *AuthorIDs: 1983005719 and 2556241304*
```
  GET paperauthoraffiliations/_search
  {
    "query": {
      "terms" : {
        "AuthorId" : [1983005719,2556241304]
      }
    }
  }
```

- Search all coauthors of *paper 2758385003* and sort them by *AuthorSequenceNumber*.
```
  GET paperauthoraffiliations/_search
  {
    "sort" : "AuthorSequenceNumber",
    "_source": ["AuthorId", "AffiliationId"],
    "query": {
      "terms" : {
        "PaperId" : [2758385003]
      }
    }
  }
```

#### See below for more information

* [Bool Query](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-bool-query.html)
* [Types of multi_match query](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-multi-match-query.html#multi-match-types)
* [Query and filter context](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-filter-context.html)
* [Full text queries](https://www.elastic.co/guide/en/elasticsearch/reference/current/full-text-queries.html)
* [Compound queries](https://www.elastic.co/guide/en/elasticsearch/reference/current/compound-queries.html)
