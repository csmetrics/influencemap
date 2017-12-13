import sqlite3 as sql
from datetime import datetime
import sys

db_path = '/localdata/u5798145/influencemap/paper.db'
paa_table_name = 'paperAuthorAffiliations'
new_table_name = 'weightedPaperAuthorAffiliations'

pid_column_name = 'paperID'
aid_column_name = 'authorID'
new_column_name = 'paperWeight'

# connect to database
conn = sql.connect(db_path)
cur  = conn.cursor()
print("{}\tconnected to {}".format(datetime.now(), db_path))


### get all info for old table
##query = "SELECT sql FROM sqlite_maser WHERE type = 'table' and name = '{}'".format(paa_table_name)
##cur.execute(query)
##old_create_table_query = cur.fetchone()[0]

# create new table
print("{}\tcreating new table {} including {} as a column, using {}".format(datetime.now(), new_table_name, new_column_name, paa_table_name))
create_new_table_query = "CREATE TABLE {} AS SELECT * FROM ({} LEFT JOIN (SELECT {}, (CAST(1 AS float) / CAST(COUNT({}) AS float)) AS {} FROM {} GROUP BY {}) AS temp ON {}.{} = temp.{})".format(new_table_name, paa_table_name, pid_column_name, aid_column_name, new_column_name, paa_table_name, pid_column_name, paa_table_name, pid_column_name, pid_column_name)
print(create_new_table_query)
cur.execute(create_new_table_query)
print("{}\tfinished creating {}".format(datetime.now(), new_table_name))


'''
# create new table
print("{}\tcreating new table {} including {} as a column, using {}".format(datetime.now(), new_table_name, new_column_name, paa_table_name)
create_new_table_query = "CREATE TABLE {} AS SELECT * FROM ({} LEFT JOIN (SELECT {}, (CAST(1 AS float) / CAST(SUM({} AS float))) AS {} FROM {} GROUP BY {}) AS temp ON {}.{} = temp.{})".format(new_table_name, paa_table_name, pid_column_name, aid_column_name, new_column_name, paa_table_name, pid_column_name, paa_table_name, pid_column_name, pid_column_name)
cur.execute(create_new_table_query)
print("{}\tfinished creating {}".format(datetime.now(), new_table_name))
'''



if len(sys.argv) > 1:
    if sys.argv[1] == "drop_old":
        print("{}\tdropping {}".format(datetime.now(), paa_table_name))
        cur.execute("DROP TABLE {}".format(paa_table_name))
        print("{}\tfinished dropping table".format(datetime.now()))






# close connection
print("{}\tclosing connection".format(datetime.now()))
conn.commit()
conn.close()
print("{}\tconnection closed".format(datetime.now()))
