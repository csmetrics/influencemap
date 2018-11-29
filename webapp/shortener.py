'''
Functions for shorterning urls

'''

arg_tuples = ('pmin', 'pmax', 'cmin', 'cmax', 'selfcite', 'coauthor', 'node')

BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE36 = "0123456789abcdefghijklmnopqrstuvwxyz"


def encode(num, alphabet=BASE62):
    """
    Encode a positive number in Base X
    From Stack Overflow

    Arguments:
    - `num`: The number to encode
    - `alphabet`: The alphabet to use for encoding
    """
    if num == 0:
        return alphabet[0]
    arr = []
    base = len(alphabet)
    while num:
        num, rem = divmod(num, base)
        arr.append(alphabet[rem])
    arr.reverse()
    return ''.join(arr)


def decode(string, alphabet=BASE62):
    """
    Decode a Base X encoded string into the number
    From Stack Overflow

    Arguments:
    - `string`: The encoded string
    - `alphabet`: The alphabet to use for encoding
    """
    base = len(alphabet)
    strlen = len(string)
    num = 0

    idx = 0
    for char in string:
        power = (strlen - (idx + 1))
        num += alphabet.index(char) * (base ** power)
        idx += 1

    return num


def from_url_ext(url_ext_str):
    '''
    '''
    url_arg_list = url_ext_str.split('&amp;')

    arg_vals = list()
    for arg in url_arg_list:
        val = arg.split('=')[1]

        arg_vals.append(val)

    return tuple(arg_vals)


def to_url_ext(url_ext_arg):
    '''
    '''
    arg_str = list()
    for arg_tuple in zip(arg_tuples, url_ext_arg):
        arg_val = '='.join(arg_tuple)
        arg_str.append(arg_val)

    return '&amp;'.join(arg_str)


def hash_args(arg_tuple):
    #hash_fn = basehash.base62()

    a, b, c, d, e, f, g = arg_tuple
    conv64list = [a, b, c, d]
    conv2list = [e, f]
    newlist = []
    for arg in conv64list:
        #newlist.append(str(hash_fn.hash(arg)))
        newlist.append(str(encode(int(arg))))
    for arg in conv2list:
        if (arg == 'true'):
            newlist.append('1')
        else:
            newlist.append('0')
    newlist.append(str(encode(int(g))))
    return newlist


def unhash_args(arg_tuple):
    #hash_fn = basehash.base62()

    a, b, c, d, e, f, g = arg_tuple
    conv64list = [a, b, c, d]
    conv2list = [e, f]
    newlist = []
    for arg in conv64list:
        newlist.append(str(decode(arg)))
    for arg in conv2list:
        if (arg == '1'):
            newlist.append('true')
        else:
            newlist.append('false')
    newlist.append(str(decode(g)))
    return newlist


def shorten_id(f_id):
    '''
    '''
    print(decode(f_id[4:], BASE36))
    return encode(decode(f_id[4:], BASE36))


def unshorten_id(f_id):
    '''
    '''
    print(decode(f_id))
    print(encode(int(decode(f_id)), BASE36))
    return '?id=' + str(encode(int(decode(f_id)), BASE36))


def shorten_front(url):
    '''
    '''
    infmap, flower_url = url.split('/submit/')
    flower_vals = flower_url.split('&amp;', 1)

    short_flower = shorten_id(flower_vals[0])

    return '/redirect/'.join([infmap, short_flower])


def unshorten_url_ext(url):
    '''
    '''
    _, flower_url = url.split('/redirect/')
    flower_vals = flower_url.split('_')

    orig_flower = unshorten_id(flower_vals[0])

    if len(flower_vals) > 1:
        flower_args = flower_vals[1:]
        orig_args = to_url_ext(unhash_args(flower_args))

        orig_flower += '&amp;' + orig_args

    return '/submit/' + orig_flower
