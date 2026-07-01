# HowTo

## 1. Download OpenAlex Snapshot and Generate Text Files

> The existing code was originally designed to work with MAG data. To adapt it for OpenAlex, a new script `preprocessor.py`, was developed to convert OpenAlex data into the MAG data format.

> MAG organizes its datasets into large CSV files (e.g., `authors.txt`, `papers.txt`), while OpenAlex stores its data in JSON files, segmented by update date (e.g., `updated_date=*/part_*`). The `preprocessor.py` script processes these JSON files by extracting the necessary columns and converting them into CSV files formatted like those of MAG.

*Future Improvement*: This workflow could be optimized by enabling the direct generation of binary files from OpenAlex data, bypassing the intermediate CSV conversion. However, this enhancement has not yet been implemented.

### Download OpenAlex Snapshot

https://docs.openalex.org/download-all-data/download-to-your-machine

- Install AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
- Copy everything in the openalex S3 bucket to a local folder (requires ~300GB disk space).
    ```
    aws s3 sync "s3://openalex" "openalex-snapshot" --no-sign-request
    ```
    ```
    # Downloaded files
    openalex-snapshot/data$ ls
    authors  concepts  funders  institutions  merged_ids  publishers  sources  works
    ```

### Generate CSV files from OpenAlex snapshot

- Run `preprocessor.py`, and it will generate the following 8 files in the same directory as `openalex-snapshot/data`
    ```
    openalex-snapshot/data$
    -rw-rw-r--   1 minjeong minjeong 1.4G Nov 28 02:53 authors.txt
    -rw-rw-r--   1 minjeong minjeong 1.1M Nov 28 02:53 concepts.txt
    -rw-rw-r--   1 minjeong minjeong 1.6M Nov 28 02:53 institutions.txt
    -rw-rw-r--   1 minjeong minjeong  12G Nov 29 13:42 PaperAuthorAffiliations.txt
    -rw-rw-r--   1 minjeong minjeong  20G Nov 30 00:05 PaperFieldsOfStudy.txt
    -rw-rw-r--   1 minjeong minjeong  31G Nov 29 02:29 PaperReferences.txt
    -rw-rw-r--   1 minjeong minjeong 3.8M Nov 28 02:54 sources.txt
    -rw-rw-r--   1 minjeong minjeong 5.6G Nov 28 12:09 works.txt
    ```

## 2. Build the Binary Graph from CSV files

### Run `builder.py` andn it will build binary graphs from reading CSV files.
    ```
    ~/influencemap/konigsberg$ python builder.py
    (0/7) making entity id to index map
    (1/7) making paper id to index map
    (2/7) loading MAG graph
    (3/7) converting MAG IDs to internal indices
    (4/7) writing edges: entities -> papers
    (5/7) writing edges: papers -> entities
    (6/7) writing edges: papers -> citors, citees
    (7/7) done
    ```

The resulting binary graph consists of 15 files, as listed below, with a total size of approximately 88GB.

    ```
    ~/influencemap/konigsberg/bingraph-openalex$ ll -lh
    total 88G
    drwxrwxr-x 2 dongwoo dongwoo 4.0K Dec  2 02:07 ./
    drwxrwxr-x 4 dongwoo dongwoo 4.0K Dec 25 12:52 ../
    -rw-rw-r-- 1 dongwoo dongwoo 2.0M Jan  1 13:57 affltn-id2ind.bin
    -rw-rw-r-- 1 dongwoo dongwoo 2.0G Jan  1 13:57 author-id2ind.bin
    -rw-rw-r-- 1 dongwoo dongwoo 777M Jan  1 13:57 entities-ind2id.bin
    -rw-rw-r-- 1 dongwoo dongwoo  20G Jan  1 15:03 entity2paper-ind.bin
    -rw-rw-r-- 1 dongwoo dongwoo 777M Jan  1 14:59 entity2paper-ptr.bin
    -rw-rw-r-- 1 dongwoo dongwoo   71 Jan  1 13:57 entity-counts.json
    -rw-rw-r-- 1 dongwoo dongwoo 1.0M Jan  1 13:57 fos-id2ind.bin
    -rw-rw-r-- 1 dongwoo dongwoo 4.0M Jan  1 13:57 journl-id2ind.bin
    -rw-rw-r-- 1 dongwoo dongwoo  39G Jan  1 15:12 paper2citor-citee-ind.bin
    -rw-rw-r-- 1 dongwoo dongwoo 3.9G Jan  1 15:12 paper2citor-citee-ptr.bin
    -rw-rw-r-- 1 dongwoo dongwoo  20G Jan  1 15:06 paper2entity-ind.bin
    -rw-rw-r-- 1 dongwoo dongwoo 2.0G Jan  1 15:04 paper2entity-ptr.bin
    -rw-rw-r-- 1 dongwoo dongwoo 4.0G Jan  1 14:03 paper-id2ind.bin
    -rw-rw-r-- 1 dongwoo dongwoo 2.0G Jan  1 14:03 paper-ind2id.bin
    -rw-rw-r-- 1 dongwoo dongwoo  25K Jan  1 14:03 paper-years.json
    ```


## 3. Build the ID→Name Binary Files

Run `id2name_builder.py` after `builder.py`. It reads the display-name/title columns added by the preprocessor and emits:

- `entity-name-ptr.bin` + `entity-name-dat.bin` — display names for authors, institutions, concepts, and sources, concatenated in the same order as `entities-ind2id.bin`. **Required** — used on every flower render.
- `paper-title-ptr.bin` + `paper-title-dat.bin` — paper titles in `paper-ind2id.bin` order. **Deprecated**: skip with `--skip-papers`. Paper titles will move to OpenSearch; the 54 GB paper-title mmap put too much pressure on the page cache and slowed cold-cache flower requests. Florist tolerates missing files (returns empty title from `get_paper_info`).

```
~/influencemap/konigsberg$ python id2name_builder.py \
    --csv-dir /data_seoul/openalex/openalex-snapshot/data \
    --bingraph bingraph-openalex \
    --skip-papers
```

Notes:
- With `--skip-papers` the entity name build finishes in minutes (small files). Full works.txt title indexing (if you re-enable it) takes hours.
- `--skip-entities` / `--skip-papers` let you build one set at a time.
- Idempotent: re-running overwrites existing `*-name-*.bin` and `*-title-*.bin` files.

Expected file sizes (full OpenAlex snapshot, ~500M works, ~95M authors):

| File | Approx size |
|---|---|
| `entity-name-ptr.bin` | ~800 MB |
| `entity-name-dat.bin` | ~5 GB |
| `paper-title-ptr.bin` | ~4 GB |
| `paper-title-dat.bin` | ~50 GB |

After this step, copy/sync the entire `bingraph-openalex/` directory back to the deploy server.

## 4. Index Search Data into OpenSearch

OpenSearch powers typeahead search (replaces the old OpenAlex `/search` API call) and paper-title lookups for tooltips (replaces the deprecated `paper-title-*.bin`).

Start OpenSearch (defined in `compose.yaml` at repo root):

```
docker compose up -d opensearch
docker compose exec webapp curl -s http://opensearch:9200/_cluster/health
```

Run the indexer from any host with the `.txt` files accessible and network reach to OpenSearch. From inside the webapp container is easiest — it already has `opensearch-py` installed:

```
docker compose exec webapp python -m scripts.index_to_opensearch \
    --url http://opensearch:9200 \
    --data-dir /path/to/openalex-snapshot/data
```

Per-entity sizing and expected duration on NVMe (rough):

| Entity | Docs | Duration | On-disk index |
|---|---|---|---|
| `institutions` | ~110K | seconds | <100 MB |
| `concepts`     | ~65K  | seconds | <100 MB |
| `sources`      | ~250K | seconds | <100 MB |
| `authors`      | ~95M  | 1–2 h   | ~30 GB |
| `works`        | ~500M | 12–36 h | ~100–150 GB |

Flags:
- `--entity <type>` — index just one type (default: `all`).
- `--chunk-size N` — bulk size (default 5000).
- `--recreate` — delete the currently-aliased index for this entity before indexing.
- `--delete-old` — after alias swap, remove previous versioned indexes.

Indexer produces versioned index names (`authors_v20260701_140000`, …) and swaps a stable alias (`authors`, `works`, …) atomically on completion, so live queries never see a half-built index.

## 5. Run the Scoring Engine

Run the konigsberg app on port 8081.
```
flask run --host=0.0.0.0 --port=8081
# nohup flask run --host=0.0.0.0 --port=8081 &
```
