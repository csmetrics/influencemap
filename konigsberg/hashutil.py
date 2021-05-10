import mmap
import pathlib

import numba as nb
import numpy as np


@nb.njit(nogil=True)
def _make_hash_map(ids, id2index):
    for i, id_ in enumerate(ids):
        # Pretty bad hashing method, but our IDs are already almost
        # uniform, they just need a little bit of help :)
        id_ = nb.u4(id_ * nb.u4(0x9e3779b1))
        id_ = nb.u4(id_ & nb.u4(0x0fffffff))
        while id2index[id_] != nb.u4(-1):
            id_ = nb.u4(nb.u4(id_ + 1) & nb.u4(0x0fffffff))
        id2index[id_] = i


def make_id_hash_map(np_ids, path):
    path = pathlib.Path(path)
    path.mkdir(exist_ok=True)
    with open(path / 'id2index.bin', 'wb+') as f:
        f.write(np.full(1 << len(np_ids).bit_length(), -1, np.uint32))
        f.flush()
        id2index_mmap = mmap.mmap(f.fileno(), 0)
    with id2index_mmap:
        id2index = np.frombuffer(id2index_mmap, dtype=np.uint32)
        _make_hash_map(np_ids, id2index)
    with open(path / 'index2id.bin', 'wb+') as f:
        f.write(np_ids)
