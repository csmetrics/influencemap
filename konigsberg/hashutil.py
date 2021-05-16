import mmap

import numba as nb
import numpy as np

SENTINEL = np.uint32(-1)


@nb.njit(nogil=True)
def _convert_in2ind_inplace(id2ind, ind2id, id2ind_len, arr, allow_missing):
    for i, id_ in enumerate(arr):
        if id_ != SENTINEL:
            hash_ = nb.u4(id_ * nb.u4(0x9e3779b1))
            hash_ %= id2ind_len
            while True:
                index = id2ind[hash_]
                if index == SENTINEL:
                    if allow_missing:
                        arr[i] = SENTINEL
                        break
                    else:
                        raise KeyError('id not found')
                if ind2id[index] == id_:
                    arr[i] = index
                    break
                hash_ += 1
                if hash_ >= id2ind_len:
                    hash_ -= id2ind_len


class Ind2IdMap:
    def __init__(self, path):
        with open(path, 'rb') as f:
            self.ind2id_mmap = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        self.ind2id = np.frombuffer(self.ind2id_mmap, dtype=np.uint32)

    def __del__(self):
        self.ind2id_mmap.close()
    

class Id2IndHashMap:
    def __init__(self, path, ind2id_map):
        with open(path, 'rb') as f:
            self.id2ind_mmap = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        self.id2ind = np.frombuffer(self.id2ind_mmap, dtype=np.uint32)
        self.ind2id_map = ind2id_map

    def __del__(self):
        self.id2ind_mmap.close()

    def convert_inplace(self, series, allow_missing=False):
        arr = series.to_numpy()
        _convert_in2ind_inplace(
            self.id2ind, self.ind2id_map.ind2id,
            nb.literally(len(self.id2ind)),
            arr, nb.literally(allow_missing))

    def __del__(self):
        self.close()

    def close(self):
        if self.id2ind_mmap:
            self.id2ind_mmap.close()
        self.id2ind_mmap = None
        self.id2ind = None
        self.ind2id_map = None

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


@nb.njit(nogil=True)
def _make_hash_map(ids, id2ind, arr_size, offset):
    for i, id_ in enumerate(ids):
        # Pretty bad hashing method, but our IDs are already almost
        # uniform, they just need a little bit of help :)
        # Hashing method due to Knuth.
        id_ = nb.u4(id_ * nb.u4(0x9e3779b1))
        id_ = id_ % arr_size
        while id2ind[id_] != SENTINEL:
            id_ += 1
            if id_ >= arr_size:
                id_ -= arr_size
        id2ind[id_] = i + offset


def get_hash_map_size(i):
    i += i // 2
    return 1 << i.bit_length()


def make_id_hash_map(ids, path, offset=0):
    with open(path, 'wb+') as f:
        f.seek(get_hash_map_size(len(ids)) * np.uint32().nbytes - 1)
        f.write(b'\x00')
        f.flush()
        id2ind_mmap = mmap.mmap(f.fileno(), 0)
    with id2ind_mmap:
        id2ind = np.frombuffer(id2ind_mmap, dtype=np.uint32)
        id2ind[...] = SENTINEL
        arr_size = len(id2ind)
        _make_hash_map(ids, id2ind, nb.literally(arr_size), offset)
