import os
import csv
import json
import gzip
import logging
import pathlib

import pandas as pd

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

PREFIX_WORK = "https://openalex.org/W"
PREFIX_AUTHOR = "https://openalex.org/A"
PREFIX_INST = "https://openalex.org/I"
PREFIX_FOS = "https://openalex.org/C"
PREFIX_SOURCE = "https://openalex.org/S"

class OpenAlexDialect(csv.Dialect):
    """Open Alex Graph table file format."""
    delimiter = '\t'
    doublequote = False
    escapechar = None
    lineterminator = '\r\n'
    quotechar = None
    quoting = csv.QUOTE_NONE
    skipinitialspace = False
    strict = True


def load_merged_ids(data_path, data_type, split_char):
    path = data_path / 'merged_ids' / data_type
    if not os.path.exists(path):
        return {}

    id_list = []
    for file_name in os.listdir(path):
        if file_name.endswith('.csv.gz'):
            file_path = os.path.join(path, file_name)
            try:
                df = pd.read_csv(file_path, compression='gzip')
                id_list.extend(df['id'].str.lstrip(split_char).tolist())
            except Exception as e:
                print(f"Error reading file {file_name}: {e}")

    id_set = set(id_list)
    logger.info('...merged_ids {} {}'.format(data_type, len(id_set)))
    return id_set


OUT_SUFF = '.txt'
def generate_entity_files(data_path, data_type, split_char):
    merged_ids = load_merged_ids(data_path, data_type, split_char)

    path = data_path / data_type
    part_files = path.glob('updated_date=*/part_*.gz')
    outfile = data_path / (data_type + OUT_SUFF)

    logger.info('...generating {} {}'.format(data_type, split_char))
    names = ['id', 'works_count']
    with open(outfile, 'w') as csvfile:
        csvwriter = csv.writer(csvfile, dialect=OpenAlexDialect())
        csvwriter.writerow(names)
        for file in part_files:
            try:
                # Read and process each file
                with gzip.open(file, 'rt', encoding='utf-8') as f:
                    data = [
                        [
                            json_data['id'].split(split_char)[1] if 'id' in json_data and json_data['id'].split(split_char)[1] not in merged_ids else None,
                            json_data['works_count']
                        ]
                        for line in f
                        if (json_data := json.loads(line))  # Parse JSON
                    ]
                    # Filter out rows with None values
                    data = [row for row in data if row[0] is not None]
                    csvwriter.writerows(data)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON in file {file}: {e}")
            except Exception as e:
                print(f"Error processing file {file}: {e}")
    logger.info('...done {} {}'.format(data_type, split_char))


def generate_works_file(data_path):
    data_type = 'works'
    split_char = 'W'
    path = data_path / data_type
    outfile = data_path / (data_type + OUT_SUFF)
    merged_ids = load_merged_ids(data_path, data_type, split_char)

    logger.info('...generating {} {}'.format(data_type, split_char))
    names=['paper_id', 'rank', 'year', 'journal_id']
    part_files = path.glob('updated_date=*/part_*.gz')

    with open(outfile, 'w') as csvfile:
        csvwriter = csv.writer(csvfile, dialect=OpenAlexDialect())
        csvwriter.writerow(names)

        for file in part_files:
            with gzip.open(file, 'rt', encoding='utf-8') as f:
                data = [
                    [
                        json_data['id'][len(PREFIX_WORK):],
                        json_data['cited_by_count'],
                        json_data['publication_year'],
                        (
                            json_data.get('primary_location', {})
                            .get('source', {})
                            .get('id', '')
                        )[len(PREFIX_SOURCE):] if json_data.get('primary_location') and json_data.get('primary_location').get('source') else ''
                    ]
                    for line in f
                    if (json_data := json.loads(line)) and 
                    json_data['id'][len(PREFIX_WORK):] not in merged_ids
                ]
                csvwriter.writerows(data)
        
    logger.info('...done {} {}'.format(data_type, split_char))


def generate_paper_references(data_path):
    data_type = 'works'
    split_char = 'W'
    path = data_path / data_type
    outfile = data_path / ("PaperReferences" + OUT_SUFF)
    merged_ids = load_merged_ids(data_path, data_type, split_char)

    logger.info('...generating PaperReferences')
    # names=['citor_id', 'citee_id']

    part_files = path.glob('updated_date=*/part_*.gz')
    for file in part_files:
        batch_data = []  # Accumulate rows to minimize I/O operations

        with gzip.open(file, 'rt', encoding='utf-8') as f:
            for line in f:
                try:
                    json_data = json.loads(line)
                except json.JSONDecodeError:
                    print(f"Error parsing JSON in file {file}: {line.strip()}")
                    continue

                try:
                    citor_id_url = json_data.get('id')
                    if not citor_id_url:
                        continue
                    citor_id = citor_id_url[len(PREFIX_WORK):]
                    if citor_id in merged_ids:
                        continue

                    referenced_works = json_data.get('referenced_works') or []
                    if not referenced_works:
                        continue

                    referenced = [
                        rw[len(PREFIX_WORK):] for rw in referenced_works if rw
                    ]

                    batch_data.extend(
                        {'citor_id': citor_id, 'citee_id': citee_id}
                        for citee_id in referenced if citee_id not in merged_ids)
                except Exception as e:
                    print(f"Unexpected error in file {file}: {e}")

        # Write accumulated rows to CSV in one go
        if batch_data:
            df_part = pd.DataFrame(batch_data)
            df_part.to_csv(outfile, mode='a', index=False, header=False)

    logger.info('...done')


def generate_paper_authorships(data_path):
    data_type = 'works'
    split_char = 'W'
    path = data_path / data_type
    outfile = data_path / ("PaperAuthorAffiliations" + OUT_SUFF)
    merged_ids = load_merged_ids(data_path, data_type, split_char)

    logger.info('...generating PaperAuthorAffiliations')
    # names=['paper_id', 'author_id', 'affiliation_id']
    part_files = path.glob('updated_date=*/part_*.gz')
    for file in part_files:
        batch_data = []

        with gzip.open(file, 'rt', encoding='utf-8') as f:
            for line in f:
                try:
                    json_data = json.loads(line)
                except json.JSONDecodeError:
                    print(f"Error parsing JSON in file {file}: {line.strip()}")
                    continue

                paper_id_url = json_data.get('id')
                if not paper_id_url:
                    continue
                paper_id = paper_id_url[len(PREFIX_WORK):]
                if paper_id in merged_ids:
                    continue

                for a in json_data.get('authorships', []):
                    try:
                        author = a.get('author') or {}
                        author_id_url = author.get('id')
                        if not author_id_url:
                            continue
                        author_id = author_id_url[len(PREFIX_AUTHOR):]

                        institution_ids = [
                            inst['id'][len(PREFIX_INST):]
                            for inst in a.get('institutions', [])
                            if inst.get('id')
                        ]

                        if not institution_ids:
                            batch_data.append({'paper_id': paper_id, 'author_id': author_id, 'affiliation_id': ''})
                        else:
                            batch_data.extend([
                                {'paper_id': paper_id, 'author_id': author_id, 'affiliation_id': inst}
                                for inst in institution_ids
                            ])
                    except Exception as e:
                        print(f"Unexpected error in file {file}: {e} in paper {paper_id}")

        # Write batch to CSV
        if batch_data:
            df_part = pd.DataFrame(batch_data)
            df_part.to_csv(outfile, mode='a', index=False, header=False)

    logger.info('...done')


def generate_paper_fos(data_path):
    data_type = 'works'
    split_char = 'W'
    path = data_path / data_type
    outfile = data_path / ("PaperFieldsOfStudy" + OUT_SUFF)
    merged_ids = load_merged_ids(data_path, data_type, split_char)

    logger.info('...generating PaperFieldsOfStudy')
    # names=['paper_id', 'fos_id']
    part_files = path.glob('updated_date=*/part_*.gz')
    for file in part_files:
        batch_data = []

        with gzip.open(file, 'rt', encoding='utf-8') as f:
            for line in f:
                try:
                    json_data = json.loads(line)
                except json.JSONDecodeError:
                    print(f"Error parsing JSON in file {file}: {line.strip()}")
                    continue

                try:
                    paper_id_url = json_data.get('id')
                    if not paper_id_url:
                        continue
                    paper_id = paper_id_url[len(PREFIX_WORK):]
                    if paper_id in merged_ids:
                        continue

                    concepts = []
                    for c in json_data.get('concepts', []):
                        level = c.get('level')
                        if level is None or level > 1:
                            continue
                        fos_id_url = c.get('id')
                        if not fos_id_url:
                            continue
                        concepts.append(fos_id_url[len(PREFIX_FOS):])

                    if not concepts:
                        continue

                    batch_data.extend({'paper_id': paper_id, 'fos_id': fos_id} for fos_id in concepts)
                except Exception as e:
                    print(f"Unexpected error in file {file}: {e}")

        # Write accumulated rows to CSV
        if batch_data:
            df_part = pd.DataFrame(batch_data)
            df_part.to_csv(outfile, mode='a', index=False, header=False)
    logger.info('...done')


def generate_text_files(data_path):
    """Run the script, reading from in_path and writing to out_path."""
    data_path = pathlib.Path(data_path)

    logger.info('(0/5) read and generate entity files')
    for path_type, split_char in [
        ['authors', 'A'],
        ['institutions', 'I'],
        ['concepts', 'C'],
        ['sources', 'S'],
    ]:
        generate_entity_files(data_path, path_type, split_char)

    logger.info('(1/5) read and generate work files')
    generate_works_file(data_path)

    logger.info('(2/5) create PaperReferences')
    generate_paper_references(data_path)

    logger.info('(3/5) create PaperAuthorAffiliations')
    generate_paper_authorships(data_path)

    logger.info('(4/5) create PaperFieldsOfStudy')
    generate_paper_fos(data_path)

    logger.info('(5/5) done')


def main():
    """Run the script, proprocess the OpenAlex format data into MAG format."""
    stream_handler = logging.StreamHandler()  # Log to stderr.
    try:
        logger.addHandler(stream_handler)
        generate_text_files('/data_seoul/openalex/openalex-snapshot/data/')
        # generate_text_files('/Users/minjeong.shin/Work/openalex/openalex-snapshot/data/')
    finally:
        logger.removeHandler(stream_handler)


if __name__ == '__main__':
    main()