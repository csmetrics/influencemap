import mmap

import numba as nb
import numpy as np


@nb.jit(nb.void(nb.u4[::1], nb.u4[::1]), nopython=True, nogil=True)
def make_counts(indptr_arr, from_arr):
    for i in from_arr:
        indptr_arr[i] += 1

    cumul = 0
    for i in range(len(indptr_arr)):
        cumul += indptr_arr[i]
        indptr_arr[i] = cumul


@nb.jit(nb.void(nb.u4[::1], nb.u4[::1], nb.u4[::1], nb.u4[::1]),
        nopython=True, nogil=True, parallel=True)
def place_indices(indptr_arr, indices_arr, from_arr, to_arr):
    for i, j in zip(from_arr, to_arr):
        index = indptr_arr[i]
        index -= 1
        indptr_arr[i] = index
        indices_arr[index] = j

    for i in nb.prange(len(indptr_arr) - 1):
        start = indptr_arr[i]
        end = indptr_arr[i + 1]
        if end > start + 1:
            indices_arr[start:end].sort()


def make_sparse_matrix(from_series, to_series, n_from_ids, path):
    path.mkdir(exist_ok=True)
    with open(path / 'indptr.bin', 'wb+') as f_indptr:
        f_indptr.write(np.zeros(n_from_ids + 1, dtype=np.uint32))
        f_indptr.flush()
        map_indptr = mmap.mmap(f_indptr.fileno(), 0)
    with map_indptr:
        arr_indptr = np.frombuffer(map_indptr, dtype=np.uint32)
        print('counting')
        make_counts(arr_indptr, from_series.to_numpy())
        with open(path / 'indices.bin', 'wb+') as f_indices:
            f_indices.write(np.zeros(len(from_series), dtype=np.uint32))
            f_indices.flush()
            map_indices = mmap.mmap(f_indices.fileno(), 0)
        with map_indices:
            arr_indices = np.frombuffer(map_indices, dtype=np.uint32)
            print('placing')
            place_indices(arr_indptr, arr_indices,
                          from_series.to_numpy(), to_series.to_numpy())


@nb.jit(nb.void(nb.u4[::1], nb.u4[::1], nb.u4[::1]),
        nopython=True, nogil=True, parallel=True)
def place_vec(vec_arr, from_arr, to_arr):
    for i in nb.prange(len(from_arr)):
        from_index = from_arr[i]
        to_index = to_arr[i]
        vec_arr[from_index] = to_index


def make_sparse_vector(from_series, to_series, n_from_ids, path):
    with open(path, 'wb+') as f:
        f.write(np.full(n_from_ids, np.uint32(-1), dtype=np.uint32))
        f.flush()
        vec_mmap = mmap.mmap(f.fileno(), 0)
    with vec_mmap:
        vec_arr = np.frombuffer(vec_mmap, dtype=np.uint32)
        place_vec(vec_arr, from_series.to_numpy(), to_series.to_numpy())
