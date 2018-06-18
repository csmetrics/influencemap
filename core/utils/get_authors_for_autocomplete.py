'''

   this script is used to get a list of authors that have published 
   many of the papers in the database to be used as the source for 
   the search autocomplete on the webapp

   Ben Readshaw
   17-1-18

'''

import sqlite3
from datetime import datetime


def main():
	database = '/localdata/u5798145/influencemap/paper.db'
	textinfile = '/localdata2/data/Authors.txt'
	textoutfile = '/home/u5798145/influencemap/webapp/webapp/cache/authorsListNew.txt'

	conn = sqlite3.connect(database)
	cur = conn.cursor()

	paa_tablename = 'PAA'
	author_tablename = 'authors'

	# get ids of top authors
	query = 'select authorID, count(distinct paperID) from PAA group by 1 order by 2 desc limit 600000' 
	print(str(datetime.now()) + " starting query:\n\t"+query)
	cur.execute(query)
	result_ids = cur.fetchall()
	print(str(datetime.now())+"finished executing query, lowest author had "+str(result_ids[-1][1])+"papers")
	result_ids = set([x[0] for x in result_ids])

	conn.close()

	# get names of authors
	firstLine = True
	print(str(datetime.now())+ " writing to file")
	with open(textinfile, 'r') as infile:
		with open(textoutfile, 'w') as outfile:
			for line in infile:
				aid, name = line.split('\t')
				if aid in result_ids:
					toWrite = ("" if firstLine else "") + name
					firstLine = False
					outfile.write(toWrite)
	print(str(datetime.now())+" finished writing to file")


if __name__ == '__main__':
	main()
