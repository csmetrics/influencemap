import sqlite3
import os
from datetime import datetime 
from construct_db_func import build_coltype, construct_table, import_to_table, create_index
from construct_db_papers import construct_papers
from construct_db_paa import construct_paa
from construct_db_authname import construct_authname
from construct_db_confname import construct_confname
from construct_db_affiname import construct_affiname

# Input data directory
data_dir = '/mnt/data/MicrosoftAcademicGraph/data_txt'

# database output directory
#db_dir = '/localdata/common'
db_dir = '/home/u5642715/data_loc/influenceMapOut'

db_path = os.path.join(db_dir, 'paper_info2.db')

conn = sqlite3.connect(db_path)
cur = conn.cursor()

construct_papers()
construct_paa()
construct_authname()

# Join the two constructed tables to make required paper_info table
print('{} start joining papers and paa by paper_id'.format(datetime.now()))
cur.execute('CREATE TABLE paper_info AS SELECT a.paper_id, auth_id, conf_id, affi_id FROM papers a INNER JOIN paa b ON a.paper_id = b.paper_id;')
print('{} finish joining papers and paa by paper_id'.format(datetime.now()))
     
# Save
conn.commit()
conn.close()
