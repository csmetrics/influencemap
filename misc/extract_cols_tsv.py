import csv
import itertools
import sys


class MAGDialect(csv.Dialect):
    delimiter = '\t'
    doublequote = False
    escapechar = None
    lineterminator = '\r\n'
    quotechar = None
    quoting = csv.QUOTE_NONE
    skipinitialspace = False
    strict = True


class PostgresDialect(csv.Dialect):
    delimiter = '\t'
    doublequote = False
    escapechar = '\\'
    lineterminator = '\n'
    quotechar = None
    quoting = csv.QUOTE_NONE
    skipinitialspace = False
    strict = True


def extract(f_in, f_out, cols):
    reader = csv.reader(f_in, dialect=MAGDialect())
    writer = csv.writer(f_out, dialect=PostgresDialect())

    # Below is equivalent to (but faster than):
    # for line in reader:
    #     selected = (line[c] for c in cols)
    #     writer.writerow(selected)
    line_getitems = map(list.__getitem__.__get__, reader)
    writer.writerows(map(map, line_getitems, itertools.repeat(cols)))


if __name__ == '__main__':
    if not (2 <= len(sys.argv) <= 4):
        print(
            "Usage: python extract_cols_tsv.py "
            "comma,separated,col,numbers path_in path_out\n"
            "- indicates stdin/stdout")
        exit()

    cols = tuple(map(int, sys.argv[1].split(',')))
    if len(sys.argv) == 2:
        in_path = '-'
        out_path = '-'
    elif len(sys.argv) == 3:
        in_path = sys.argv[2]
        out_path = '-'
    else:
        in_path = sys.argv[2]
        out_path = sys.argv[3]

    f_in = open(in_path, newline='') if in_path != '-' else sys.stdin
    f_out = open(out_path, 'w', newline='') if out_path != '-' else sys.stdout

    extract(f_in, f_out, cols)
