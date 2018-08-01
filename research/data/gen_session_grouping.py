'''
Generate session grouping lists.

Date:   1st August 2018
Author: Alexander Soen
'''

import os


SESSION_FILE = 'pldi_session_grouping'

session_dir  = os.path.abspath(os.path.dirname(__file__))
session_path = os.path.join(session_dir, SESSION_FILE)


def gen_sessions():
    '''
    '''
    res_list = list()
    with open(session_path, 'r') as f:
        for line in f:
            line = [x.strip() for x in line.split(',')]
            res_list.append(line)

    return res_list
