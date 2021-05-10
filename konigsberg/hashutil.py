import mmap
import pathlib

import numba as nb
import numpy as np


@nb.njit(nogil=True)
def _make_hash_map(ids, id2index, mask):
    for i, id_ in enumerate(ids):
        # Pretty bad hashing method, but our IDs are already almost
        # uniform, they just need a little bit of help :)
        # Hashing method due to Knuth.
        id_ = nb.u4(id_ * nb.u4(0x9e3779b1))
        id_ = nb.u4(id_ & mask)
        while id2index[id_] != nb.u4(-1):
            id_ = nb.u4(nb.u4(id_ + 1) & mask)
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
        lb_arr_size = len(id2index).bit_length() - 1
        assert len(id2index) == 1 << lb_arr_size
        mask = nb.u4((1 << lb_arr_size) - 1)
        _make_hash_map(np_ids, id2index, mask)
    with open(path / 'index2id.bin', 'wb+') as f:
        f.write(np_ids)
