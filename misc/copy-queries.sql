COPY "journals" ("id", "normalized_name", "display_name")
  FROM PROGRAM 'python3 /usr/extract_cols_tsv.py 0,2,3 /data/Journals.txt'
  WITH NULL '';

COPY "conference_series" ("id", "normalized_name", "display_name")
  FROM PROGRAM 'python3 /usr/extract_cols_tsv.py 0,2,3 /data/ConferenceSeries.txt'
  WITH NULL '';

COPY "affiliations" ("id", "normalized_name", "display_name")
  FROM PROGRAM 'python3 /usr/extract_cols_tsv.py 0,2,3 /data/Affiliations.txt'
  WITH NULL '';

COPY "fields_of_study" ("id", "normalized_name", "display_name", "level")
  FROM PROGRAM 'python3 /usr/extract_cols_tsv.py 0,2,3,5 /data/FieldsOfStudy.txt'
  WITH NULL '';

COPY "authors" ("id", "normalized_name", "display_name", "last_known_affiliation_id")
  FROM PROGRAM 'python3 /usr/extract_cols_tsv.py 0,2,3,4 /data/Authors.txt'
  WITH NULL '';

-- rows: 230481032
COPY "papers_unconstr"
  FROM PROGRAM 'cut -n -f1,6,8,11,12 /data/Papers.txt | sed ''s/\\/\\\\/g'''
  WITH NULL '';

-- rows: 1561598830
COPY "citations" FROM '/data/PaperReferences.txt';
-- vacuuming

-- rows: 615980204
COPY "authorships" FROM PROGRAM 'cut -n -f1,2,3 /data/PaperAuthorAffiliations.txt' WITH NULL '';

-- rows: 1257308904
-- vacuuming
COPY "paper_fields_studied" FROM PROGRAM 'cut -n -f1,2 /data/PaperFieldsOfStudy.txt';
