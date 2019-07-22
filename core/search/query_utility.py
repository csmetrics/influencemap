'''
Utility functions for querying elasticsearch.

date:   24.06.18
author: Alexander Soen
'''

from datetime import datetime

def paper_info_to_cache_json(paper_info, additional_tag={}):
    ''' Cache a paper_info dictionary.
    '''
    # Setup meta data
    meta_json = dict()
    meta_json['_id']    = paper_info['PaperId']
    meta_json['_index'] = 'paper_info'
    meta_json['_type']  = 'doc'

    # Source data
    source = paper_info
    source['CreatedDate'] = datetime.now()
    source.update(additional_tag)

    # Return join of data
    meta_json['_source'] = source
    return meta_json


def field_del(val_dict, field):
    ''' Helper to delete a field in a dictionary without worry about a
        KeyError.
    '''
    try:
        del val_dict[field]
    except KeyError:
        pass

    return val_dict


def chunker(elements, batch_size):
    ''' Standard chunker.
    '''
    size = len(elements)
    for i in range(0, size, batch_size):
        yield elements[i: min(size, i+batch_size)]
