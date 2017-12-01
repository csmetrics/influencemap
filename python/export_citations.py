import sqlite3
import os, sys
import pandas as pd
from datetime import datetime 
import subprocess

#data_dir = '/Users/xlx/Downloads/graph-data'
data_dir = '/home/xlx/d2/MicrosoftAcademicGraph'

paper_ref_file = os.path.join(data_dir, 'data_txt', 'PaperReferences.txt')
print( '{} start reading {} ... '.format(datetime.now(), paper_ref_file))

with open(paper_ref_file, 'rt') as fh:
    paper_ref_buf = fh.read()
print( '{} load ref db {} bytes'.format(datetime.now(), sys.getsizeof(paper_ref_buf)) ) 

conf_file = os.path.join(data_dir, 'data_txt', 'Conferences.txt')
conf_df = pd.read_table(conf_file, header=None, names=['ConfID', 'Abbrv', 'FullName'])

c = sys.argv[1]
output_dir = os.path.join(data_dir, 'out', c)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

row = conf_df.loc[conf_df['Abbrv'] == c]
conf_id = list(row['ConfID'])[0]
#conf_id = '43AA5802' # "43AA5802	MM	ACM Multimedia"
conf_paper_file = os.path.join(output_dir, 'papers.'+ c +'.txt')
print( conf_id)
print(conf_paper_file)

if not os.path.exists(conf_paper_file):
    paper_file = os.path.join(data_dir, 'data_txt', 'Papers.txt')
    cmd = "grep " + conf_id +' '+ paper_file + ' > ' + conf_paper_file
    print("{} {}".format(datetime.now(), cmd) )
    os.system(cmd)

df_paper = pd.read_table(conf_paper_file, header=None, 
                         names=['PaperID', 'TitleOrig', 'TitleNorm', 'PubYear', 'PubDate', 
                               'DOI', 'VenueOrig', 'VenueNorm', 'JournalID', 'ConfID', 'PaperRank' ])
df_paper.head()
set_paper = set(df_paper['PaperID'])

print('{} papers in conference {} - {}'.format(len(set_paper), conf_id, c) )

# init output vars/files
citing_records = list()
cited_records = list()
citing_cnt = 0 
cited_cnt = 0 
ptr = 0 
line_cnt = 0
while ptr < len(paper_ref_buf):
#for i in range(len(paper_ref)):
    #  each line: ['PaperID', 'RefID']
    eol = paper_ref_buf.find('\n', ptr)
    tmp = paper_ref_buf[ptr:eol].split('\t')
    line_cnt += 1
    ptr = eol + 1

    if tmp[0] in set_paper:
        citing_records.append(tmp)
        citing_cnt += 1
    if tmp[1] in set_paper:
        cited_records.append(tmp)
        cited_cnt += 1

    if line_cnt%10000000 == 0 :
        print('{} {:9.0f} lines, found {:6.0f} citing, {:6.0f} cited'.format(datetime.now(), line_cnt, citing_cnt, cited_cnt) )
        if line_cnt >= 1e9:
            break

print('{} {:9.0f} lines, found {:6.0f} citing, {:6.0f} cited'.format(datetime.now(), line_cnt, citing_cnt, cited_cnt) )

citing_file = os.path.join(output_dir, 'citing.'+c+'.txt')
with open(citing_file, 'wt') as fh:
    fh.write('\n'.join(['\t'.join(s) for s in citing_records] ))

cited_file = os.path.join(output_dir, 'cited.'+c+'.txt')
with open(cited_file, 'wt') as fh:
    fh.write('\n'.join(['\t'.join(s) for s in cited_records] ))

print(' saved to {} and {} \n\n'.format(citing_file, cited_file))
