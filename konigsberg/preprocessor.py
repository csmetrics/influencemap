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
    part_files = path.glob('updated_date=*/part_*')
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
                        'paper_id': json_data['id'].split(split_char)[1],
                        'rank': json_data['cited_by_count'],
                        'year': json_data['publication_year'],
                        'journal_id': ''
                    }
                    try:
                        filtered_data['journal_id'] = json_data['primary_location']['source']['id'].split('S')[1]
                    except:
                        pass
                    # print(filtered_data)
                    data.append(list(filtered_data.values()))
                except json.JSONDecodeError:
                    print(f"Error parsing JSON: {line}")
            csvwriter.writerows(data)
    logger.info('...done {} {}'.format(data_type, split_char))


def generate_text_files(data_path):
    """Run the script, reading from in_path and writing to out_path."""
    data_path = pathlib.Path(data_path)

    logger.info('(0/2) read and generate entity files')
    for path_type, split_char in [
        ['authors', 'A'],
        ['institutions', 'I'],
        ['concepts', 'C'],
        ['sources', 'S'],
    ]:
        generate_entity_files(data_path, path_type, split_char)

    logger.info('(1/2) read and generate work files')
    generate_works_file(data_path)

    logger.info('(2/2) done')


def main():
    """Run the script, proprocess the OpenAlex format data into MAG format."""
    stream_handler = logging.StreamHandler()  # Log to stderr.
    try:
        logger.addHandler(stream_handler)
        # generate_text_files('/esdata/openalex/openalex-snapshot/data/')
        generate_text_files('/Users/minjeong.shin/Work/openalex/openalex-snapshot/data/')
    finally:
        logger.removeHandler(stream_handler)


if __name__ == '__main__':
    main()