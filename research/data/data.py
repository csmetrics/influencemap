'''
Parse datafiles.

date:   04.07.18
author: Alexander Soen
'''

import os
import pandas as pd

from core.config import *
from core.search.mag_interface import *
from core.search.parse_academic_search import or_query_builder_list

MAS_URL_PREFIX = "https://api.labs.cognitive.microsoft.com"

rename_dict = { 'name'     : 'AuthorName',
                'Q'        : 'QScore',
                'paper'    : 'NumberPapers',
                'citations': 'CitationCountVector' }

def get_q_data(path):
    ''' Get and format data.
    '''
    df = pd.read_csv(path, sep='\t')
    df = df[ list(rename_dict.keys()) ]
    df = df.rename(columns = rename_dict)
    return df


def get_author_ids(names):
    ''' Generate a list of author ids associated to a list of names.
    '''
    url = os.path.join(MAS_URL_PREFIX, "academic/v1.0/evaluate")
    queries = (lambda x: {
        'expr': expr,
        'count': 10000,
        'offset': x,
        'attributes': 'Id,AuN'
        } for expr in or_query_builder_list("AuN='{}'", names))

    results = dict()

    test = 0

    for query in queries:
        test += 1

        # Check offset
        finished = False
        count    = 0

        while not finished:
            data = query_academic_search('get', url, query(count))

            # Check if no more data
            if len(data['entities']) > 0:
                count += len(data['entities'])
            else:
                finished = True

            for res in data['entities']:
                # Check if key exists
                if not res['AuN'] in results:
                    results[res['AuN']] = list()

                results[res['AuN']].append(res['Id'])

    return results
