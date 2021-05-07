import mmap

import numba as nb
import numpy as np


ro_array = nb.types.Array(nb.u4, 1, 'C', readonly=True)

@nb.jit(nb.types.Tuple([nb.u4[::1], nb.f4[::1]])(
            ro_array, ro_array, nb.u4[::1], nb.f4[::1]),
        nopython=True, nogil=True)
def _traverse(indptr, indices, origins, origins_mul):
    sinks = nb.typed.Dict.empty(key_type=nb.u4, value_type=nb.f4)
    for v, m in zip(origins, origins_mul):
        start = indptr[v]
        end = indptr[v + 1]
        for i in indices[start:end]:
            sinks[i] = sinks.get(i, nb.f4(0.)) + m
    res_indices = np.empty(len(sinks), dtype=np.uint32)
    res_mul = np.empty(len(sinks), dtype=np.float32)
    for i, (s, m) in enumerate(sinks.items()):
        res_indices[i] = s
        res_mul[i] = m
    return res_indices, res_mul


class Graph:
    __slots__ = ['indptr', 'indices', 'indptr_mmap', 'indices_mmap']

    def __init__(self, indptr_path, indices_path):
        with open(indptr_path, 'rb') as f:
            self.indptr_mmap = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        self.indptr = np.frombuffer(self.indptr_mmap, dtype=np.uint32)
        with open(indices_path, 'rb') as f:
            self.indices_mmap = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        self.indices = np.frombuffer(self.indices_mmap, dtype=np.uint32)

    def __del__(self):
        self.indptr_mmap.close()
        self.indices_mmap.close()

    def traverse(self, origins, origins_mul=None):
        if origins_mul is None:
            origins_mul = np.ones_like(origins, dtype=np.float32)
        return _traverse(self.indptr, self.indices, origins, origins_mul)
