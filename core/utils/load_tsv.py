import sys

def tsv_to_dict(filename):
    data = []
    with open(filename, 'r') as fh:
        headers = fh.readline().strip().split('\t')
        rows = fh.readlines()
    for row in rows:
        row_dict = {}
        row = row.strip().split('\t')
        for i in range(len(headers)):
            row_dict[headers[i]] = row[i]
        data.append(row_dict)
    return data
if __name__ == "__main__":
    tsv_to_dict(sys.argv[1])
