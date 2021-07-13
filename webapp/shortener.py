import collections
import itertools
import string
from base64 import urlsafe_b64decode, urlsafe_b64encode

order_list = ("ratio", "blue", "red", "total")
BASE62 = f'{string.digits}{string.ascii_lowercase}{string.ascii_uppercase}'


def decode(string):
    res = 0
    for char in string:
        res = res * len(BASE62) + BASE62.index(char)
    return res


Filters = collections.namedtuple(
    'Filters',
    ['pub_years', 'cit_years', 'self_citations', 'coauthors',
     'num_nodes', 'order', 'cmp_ref'])


def decode_filters(short_filters):
    a, b, c, d, e, f, g, h, i = short_filters.split('_')
    return Filters(pub_years=(decode(a), decode(b)),
                   cit_years=(decode(c), decode(d)),
                   self_citations=e == '1',
                   coauthors=f == '1',
                   num_nodes=decode(g),
                   order=order_list[int(h)],
                   cmp_ref=i == '1')


KIND_BITS = 4
ID_BITS = 32
ID_MASK = (1 << ID_BITS) - 1
ID_WITH_KIND_CHARS = (ID_BITS + KIND_BITS + 5) // 6
ID_WITH_KIND_BYTES = (ID_BITS + KIND_BITS + 7) // 8
BIT_PADDING = ID_WITH_KIND_BYTES * 8 - (ID_BITS + KIND_BITS)
PARTIAL_BYTE = bool(BIT_PADDING)
PADDING = ('A' * PARTIAL_BYTE) + '=' * (-ID_WITH_KIND_CHARS % 4 - PARTIAL_BYTE)


def url_decode_id(id_with_kind_b64):
    id_with_kind_b64 = id_with_kind_b64 + PADDING
    id_with_kind_bytes = urlsafe_b64decode(id_with_kind_b64)
    id_with_kind = int.from_bytes(id_with_kind_bytes, 'big')
    id_with_kind >>= BIT_PADDING
    kind = id_with_kind >> ID_BITS
    id_ = id_with_kind & ID_MASK
    return kind, id_


def url_encode_id(kind, id_):
    id_with_kind = (kind << ID_BITS) + id_
    id_with_kind <<= BIT_PADDING
    id_with_kind_bytes = id_with_kind.to_bytes(ID_WITH_KIND_BYTES, 'big')
    id_with_kind_b64 = urlsafe_b64encode(id_with_kind_bytes)
    return id_with_kind_b64[:ID_WITH_KIND_CHARS].decode()


# Order matters here (e.g. author->0, affiliation->1, ..., paper->5)
KINDS = ['author_ids', 'affiliation_ids', 'conference_series_ids',
         'field_of_study_ids', 'journal_ids', 'paper_ids']

IDs = collections.namedtuple('IDs', KINDS, defaults=(() for _ in KINDS))

BASE64_CHARS = f'{string.digits}{string.ascii_letters}-_'
ALL_CHARS = BASE64_CHARS + '.~'


def make_b64_padding(b64str):
    return b64str + '=' * (-len(b64str) % 4)


def url_decode_info(url_str):
    if not all(map(ALL_CHARS.__contains__, url_str)):
        raise ValueError('found invalid characters')
    encoded_ids, sep, encoded_name = url_str.partition('~')
    if not sep:
        encoded_ids, sep, encoded_name = url_str.partition('.')
    curated = sep == '~'
    encoded_name = make_b64_padding(encoded_name)
    name = urlsafe_b64decode(encoded_name).decode()
    if len(encoded_ids) % ID_WITH_KIND_CHARS:
        raise ValueError('invalid length')
    ids_res = IDs._make([] for _ in KINDS)
    for start in range(0, len(encoded_ids), ID_WITH_KIND_CHARS):
        kind, id_ = url_decode_id(
            encoded_ids[start : start+ID_WITH_KIND_CHARS])
        ids_res[kind].append(id_)
    return ids_res, name, curated


def url_encode_info(
    *,
    author_ids=(), affiliation_ids=(), conference_series_ids=(),
    field_of_study_ids=(), journal_ids=(), paper_ids=(), name=None,
    curated=False,
):
    locals_ = locals()
    encoded_ids = ''.join(url_encode_id(i, id_)
                          for i, lname in enumerate(KINDS)
                          for id_ in locals_[lname])
    name = name or ''
    sep = '~' if curated else ('.' if name else '')
    encoded_name = urlsafe_b64encode(name.encode()).decode().rstrip('=')
    res = f'{encoded_ids}{sep}{encoded_name}'
    assert all(map(ALL_CHARS.__contains__, res))
    return res
