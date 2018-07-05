'''
Utility functions for data.

date:   05.07.18
author: Alexander Soen
'''

import unidecode

def name_normalise(string):
    ''' Normalises a name string to match the api closer.
    '''
    string = string.lower()
    string = string.replace('.', '')
    string = string.replace('\'', '\\\'')
    string = unidecode.unidecode(string)
    return string
