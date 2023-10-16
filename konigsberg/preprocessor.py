import csv
import json
import logging
import pathlib

import numpy as np
import pandas as pd

import hashutil
import sparseutil

YEAR_SENTINEL = np.uint16(-1)  # Denotes missing year
INDEX_SENTINEL = np.uint64(-1)  # Denotes deleted entity

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

OUT_SUFF = '.txt'
def generate_entity_files(data_path, data_type, split_char):
    path = data_path / data_type
    part_files = path.glob('updated_date=*/part_*')
    outfile = data_path / (data_type + OUT_SUFF)

    logger.info('...generating {} {}'.format(data_type, split_char))
    names = ['id', 'works_count']
    with open(outfile, 'a') as csvfile:
        csvwriter = csv.writer(csvfile, dialect=OpenAlexDialect())
        csvwriter.writerow(names)
        for file in part_files:
            data = []
            for line in open(file, 'r'):
                try:
                    json_data = json.loads(line)
                    datum = []
                    for n in names:
                        if n == 'id':
                            datum.append(json_data[n].split(split_char)[1])
                        else:
                            datum.append(json_data[n])
                    data.append(datum)
                except json.JSONDecodeError:
                    print(f"Error parsing JSON: {line}")
            csvwriter.writerows(data)
    logger.info('...done {} {}'.format(data_type, split_char))


def generate_works_file(data_path):
    data_type = 'works'
    split_char = 'W'
    path = data_path / data_type
    outfile = data_path / (data_type + OUT_SUFF)

    logger.info('...generating {} {}'.format(data_type, split_char))
    names=['paper_id', 'rank', 'year', 'journal_id']
    part_files = path.glob('updated_date=*/part_*')

    with open(outfile, 'a') as csvfile:
        csvwriter = csv.writer(csvfile, dialect=OpenAlexDialect())
        csvwriter.writerow(names)
        for file in part_files:
            data = []
            for line in open(file, 'r'):
                try:
                    json_data = json.loads(line)
                    filtered_data = {
                        'paper_id': json_data['id'][len(PREFIX_WORK):],
                        'rank': json_data['cited_by_count'],
                        'year': json_data['publication_year'],
                        'journal_id': ''
                    }
                    try:
                        filtered_data['journal_id'] = json_data['primary_location']['source']['id'][len(PREFIX_SOURCE):]
                    except:
                        pass
                    # print(filtered_data)
                    data.append(list(filtered_data.values()))
                except json.JSONDecodeError:
                    print(f"Error parsing JSON: {line}")
            csvwriter.writerows(data)
    logger.info('...done {} {}'.format(data_type, split_char))


def generate_paper_references(data_path):
    data_type = 'works'
    path = data_path / data_type
    outfile = data_path / ("PaperReferences" + OUT_SUFF)

    logger.info('...generating PaperReferences')
    # names=['citor_id', 'citee_id']
    part_files = path.glob('updated_date=*/part_*')
    for file in part_files:
        for line in open(file, 'r'):
            try:
                json_data = json.loads(line)
                if len(json_data['referenced_works']) == 0:
                    continue

                referenced = [rw[len(PREFIX_AUTHOR):] for rw in json_data['referenced_works']]
                df_part = pd.DataFrame({
                    'citor_id': [json_data['id'][len(PREFIX_AUTHOR):]]*len(referenced),
                    'citee_id': referenced
                })
                df_part.to_csv(outfile, mode='a', index=False, header=False)
            except json.JSONDecodeError:
                print(f"Error parsing JSON: {line}")

    logger.info('...done')


def generate_paper_authorships(data_path):
    data_type = 'works'
    path = data_path / data_type
    outfile = data_path / ("PaperAuthorAffiliations" + OUT_SUFF)

    logger.info('...generating PaperAuthorAffiliations')
    # names=['paper_id', 'author_id', 'affiliation_id']
    part_files = path.glob('updated_date=*/part_*')

    for file in part_files:
        for line in open(file, 'r'):
            try:
                json_data = json.loads(line)
                paper_id = json_data['id'][len(PREFIX_WORK):]
                try:
                    authors = [a['author']['id'][len(PREFIX_AUTHOR):] for a in json_data['authorships']]
                except:
                    authors = []
                if len(authors) == 0:
                    continue

                institutions = []
                for a in json_data['authorships']:
                    inst = None
                    try:
                        inst = a['institutions'][0]['id'][len(PREFIX_INST):]
                    except:
                        pass
                    institutions.append(inst)

                df_part = pd.DataFrame({
                    'paper_id': [paper_id]*len(authors),
                    'author_id': authors,
                    'affiliation_id': institutions
                })
                df_part.to_csv(outfile, mode='a', index=False, header=False)
            except Exception as e:
                print(f"Error parsing JSON: {line}")
    logger.info('...done')


def generate_paper_fos(data_path):
    data_type = 'works'
    path = data_path / data_type
    outfile = data_path / ("PaperFieldsOfStudy" + OUT_SUFF)

    logger.info('...generating PaperFieldsOfStudy')
    # names=['paper_id', 'fos_id']
    part_files = path.glob('updated_date=*/part_*')

    for file in part_files:
        for line in open(file, 'r'):
            try:
                json_data = json.loads(line)
                paper_id = json_data['id'][len(PREFIX_WORK):]
                concepts = [c['id'][len(PREFIX_FOS):] for c in json_data['concepts'] if c['level'] <= 1]
                if len(concepts) == 0:
                    continue
                df_part = pd.DataFrame({
                    'paper_id': [paper_id]*len(concepts),
                    'fos_id': concepts
                })
                df_part.to_csv(outfile, mode='a', index=False, header=False)
            except json.JSONDecodeError:
                print(f"Error parsing JSON: {line}")
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