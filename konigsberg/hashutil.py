"""Utilities for mapping IDs to their indices.

These are implemented as a hash map with open addressing/linear probing.
See https://en.wikipedia.org/wiki/Linear_probing.
"""

import mmap

import numba as nb
import numpy as np

SENTINEL = np.uint64(-1)


@nb.njit(nogil=True)
def _convert_in2ind_inplace(id2ind, ind2id, id2ind_len, arr, allow_missing):
    """Convert IDs to indices in-place.

    id2ind is a Numpy array: a hash map mapping IDs to candidate
    indices; id2ind_len is its length. ind2id maps indices to their IDs.
    arr is the input/output array. When allow_missing is True,
    unrecognised IDs do not raise, but are instead replaced with
    SENTINEL.
    """
    for i, id_ in enumerate(arr):
        # hash_ = nb.u4(id_ * nb.u4(0x9e3779b1)) % id2ind_len
        hash_ = id_ % id2ind_len
        while True:
            index = id2ind[hash_]
            if index == SENTINEL:
                if not allow_missing:
                    raise KeyError('id not found')
                arr[i] = SENTINEL
                break
            # id2ind[hash_] might be the correct index, but this is not
            # guaranteed due to collisions. Look it up in ind2id to make
            # sure.
            if ind2id[index] == id_:
                arr[i] = index
                break
            hash_ += 1  # id2ind[hash_] was not correct. Try next cell.
            if hash_ >= id2ind_len:
                hash_ = 0  # Went past the end; wrap around.


class Ind2IdMap:
    """Map from indices to IDs.

    This is a plain NumPy array, where we retrieve the ID as
    self.ind2id[index]. The entity type is not stored.
    """

    def __init__(self, path):
        with open(path, 'rb') as f:
            self.ind2id_mmap = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        self.ind2id = np.frombuffer(self.ind2id_mmap, dtype=np.uint64)

    def __del__(self):
        self.ind2id_mmap.close()


class Id2IndHashMap:
    """Map from IDs to indices.

    A hash map maps IDs to _candidate_ indices. ind2id_map is needed to
    check whether a candidate index is the correct result.
    """

    def __init__(self, path, ind2id_map):
        with open(path, 'rb') as f:
            self.id2ind_mmap = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        self.id2ind = np.frombuffer(self.id2ind_mmap, dtype=np.uint64)
        self.ind2id_map = ind2id_map

    def __del__(self):
        self.id2ind_mmap.close()

    def convert_inplace(self, series, allow_missing=False):
        """Convert IDs to indices in-place.

        series is a Pandas series of indices. If allow_missing is set to
        True, then unrecognised IDs do not raise KeyError, but are
        instead replaced with SENTINEL.
        """
        arr = series.to_numpy()
        # nb.literally makes Numba compile once for every value.
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
        self.ind2id_map = None  # Decrease ind2id_map refcount.

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


@nb.njit(nogil=True)
def _make_hash_map(ids, id2ind, arr_size, offset):
    """Place IDs in the hash map.

    ids is a NumPy array of IDs, ordered by the index. id2ind is the
    target array; arr_size is its size. offset is a constant added to
    the indices.
    """
    for i, id_ in enumerate(ids):
        # Pretty bad hashing method (by Knuth), but our IDs are already
        # almost uniform, they just need a little bit of help :)

        hash_ = id_ % arr_size
        # hash_ = nb.u4(id_ * nb.u4(0x9e3779b1)) % arr_size
        while id2ind[hash_] != SENTINEL:  # Cell not free.
            hash_ += 1
            if hash_ >= arr_size:
                hash_ = 0  # Gone past the end; wraparound
        id2ind[hash_] = i + offset


def get_hash_map_size(i):
    """Get hash map array length from number of stored elements.

    Compute (number of stored elements * 1.5), rounded up to a power of
    2. This gives an occupancy rate between 1/3 and 2/3.
    """
    i += i // 2
    return 1 << i.bit_length()


def make_id_hash_map(ids, path, offset=0):
    """Make ID to index hash map.

    ids is an ordered NumPy array of IDs. path is the destination.
    offset is added to the indices before storing.
    """
    with open(path, 'wb+') as f:
        # Trick: seek past the end of file and write one byte to
        # efficiently zero-fill up to that point.
        f.seek(get_hash_map_size(len(ids)) * np.uint64().nbytes - 1)
        f.write(b'\x00')
        f.flush()
        id2ind_mmap = mmap.mmap(f.fileno(), 0)
    with id2ind_mmap:
        id2ind = np.frombuffer(id2ind_mmap, dtype=np.uint64)
        id2ind[...] = SENTINEL  # Important detail: set all to SENTINEL.
        arr_size = len(id2ind)
        # nb.literally causes Numba to compile the function once for
        # every value. Avoids the CPU's slow division instruction.
        _make_hash_map(ids, id2ind, nb.literally(arr_size), offset)
