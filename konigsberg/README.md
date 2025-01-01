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


## 3. Run the Scoring Engine

Run the konigsberg app on port 8081.
```
flask run --host=0.0.0.0 --port=8081
# nohup flask run --host=0.0.0.0 --port=8081 &
```
