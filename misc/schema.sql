-- Example query:
-- WITH "unique_authorships" AS (
--     SELECT DISTINCT "paper_id", "author_id"
--     FROM "authorships"
-- ), "numbers_authors" AS (
--     SELECT "paper_id", SUM(*) AS "number_authors"
--     FROM "unique_authorships"
--     GROUP BY "paper_id"
-- )
-- SELECT
--     "authors"."id" AS "influencee_id",
--     "authors"."display_name" AS "influencee_name",
--     SUM(1 / "numbers_authors"."number_authors") AS "influence_score"
-- FROM "unique_authorships" AS "unique_authorships1",
--      "numbers_authors",
--      "papers" AS "papers1",
--      "citations",
--      "papers" AS "papers2",
--      "unique_authorships" AS "unique_authorships2",
--      "authors" AS "authors",
-- WHERE "unique_authorships1"."author_id" = 342534576
--       AND "unique_authorships1"."paper_id" = "papers1"."id"
--       AND "papers1"."id" = "numbers_authors"."paper_id"
--       AND "papers1"."year" >= 1962
--       AND "papers1"."year" <= 2007
--       AND "papers1"."id" = "citations"."citee_paper_id"
--       AND "citations"."citor_paper_id" = "papers2"."id"
--       AND "papers2"."year" >= 1972
--       AND "papers2"."year" <= 2019
--       AND "papers2"."id" = "unique_authorships2"."paper_id"
--       AND "unique_authorships2"."author_id" = "authors"."id"
-- GROUP BY "authors"."id"
-- ORDER BY "influence" DESC;


-- mag/Journals.txt
CREATE TABLE "journals" (
    "id" bigint NOT NULL PRIMARY KEY,
    "normalized_name" text NOT NULL,
    "display_name" text NOT NULL
);

-- mag/ConferenceSeries.txt
CREATE TABLE "conference_series" (
    "id" bigint NOT NULL PRIMARY KEY,
    "normalized_name" text NOT NULL,
    "display_name" text NOT NULL
);

-- mag/Affiliations.txt
CREATE TABLE "affiliations" (
    "id" bigint NOT NULL PRIMARY KEY,
    "normalized_name" text NOT NULL,
    "display_name" text NOT NULL
);

-- mag/Papers.txt
CREATE TABLE "papers" (
    "id" bigint NOT NULL PRIMARY KEY,
    "title" text NOT NULL,
    "year" smallint,
    "journal_id" bigint REFERENCES "journals",
    "conference_series_id" bigint REFERENCES "conference_series"
);

-- nlp/PaperCitationContexts.txt
CREATE TABLE "citations" (
    "citor_paper_id" bigint NOT NULL REFERENCES "papers",
    "citee_paper_id" bigint NOT NULL REFERENCES "papers",
    PRIMARY KEY ("citor_paper_id", "citee_paper_id")
);

-- mag/Authors.txt
CREATE TABLE "authors" (
    "id" bigint NOT NULL PRIMARY KEY,
    "normalized_name" text NOT NULL,
    "display_name" text NOT NULL,
    "last_known_affiliation_id" bigint REFERENCES "affiliations"
);

-- mag/PaperAuthorAffiliations.txt
CREATE TABLE "authorships" (
    "paper_id" bigint NOT NULL REFERENCES "papers",
    "author_id" bigint NOT NULL REFERENCES "authors",
    "affiliation_id" bigint REFERENCES "affiliations",
    PRIMARY KEY ("paper_id", "author_id", "affiliation_id")
);

-- advanced/FieldsOfStudy.txt
CREATE TABLE "fields_of_study" (
    "id" bigint NOT NULL PRIMARY KEY,
    "normalized_name" text NOT NULL,
    "display_name" text NOT NULL,
    "level" smallint NOT NULL
);


-- advanced/PaperFieldsOfStudy.txt
CREATE TABLE "paper_fields_studied" (
    "paper_id" bigint NOT NULL REFERENCES "papers",
    "field_of_study_id" bigint NOT NULL REFERENCES "fields_of_study",
    PRIMARY KEY ("paper_id", "field_of_study_id")
);
