import mmap

import numba as nb
import numpy as np
from numba.types import List, Tuple


@nb.njit(nogil=True)
def make_counts(maps, ptr_arr):
    number_maps = len(maps)
    ptr_arr_2d = ptr_arr[:-1].reshape(-1, number_maps)
    for i, map_ in enumerate(maps):
        map_ptr = ptr_arr_2d[...,i]
        for from_arr, _ in map_:
            for j in from_arr:
                map_ptr[j] += 1

    cumul = 0
    for i in range(len(ptr_arr)):
        ptr_arr[i] = cumul = ptr_arr[i] + cumul


@nb.njit(nogil=True)
def place_indices(maps, ptr_arr, ind_arr):
    number_maps = len(maps)
    ptr_arr_2d = ptr_arr[:-1].reshape(-1, number_maps)
    for i, map_ in enumerate(maps):
        map_ptr = ptr_arr_2d[...,i]
        for from_arr, to_arr in map_:
            for j, k in zip(from_arr, to_arr):
                index = map_ptr[j] = map_ptr[j] - 1
                ind_arr[index] = k

    for i in range(len(ptr_arr) - 1):
        start = ptr_arr[i]
        end = ptr_arr[i + 1]
        if end > start + 1:
            ind_arr[start:end].sort()


def make_sparse_matrix(n_from_ids, maps, ptr_path, ind_path):
    maps = nb.typed.List([
        nb.typed.List([
            (from_series.to_numpy(), to_series.to_numpy())
            for from_series, to_series in map_])
        for map_ in maps])
    n_maps = len(maps)
    n_links = sum(sum(len(s) for s, _ in map_) for map_ in maps)
    with open(ptr_path, 'wb+') as f_ptr:
        f_ptr.seek((n_maps * n_from_ids + 1) * np.uint32().nbytes - 1)
        f_ptr.write(b'\x00')
        f_ptr.flush()
        map_ptr = mmap.mmap(f_ptr.fileno(), 0)
    with map_ptr:
        arr_ptr = np.frombuffer(map_ptr, dtype=np.uint32)
        make_counts(maps, arr_ptr)
        with open(ind_path, 'wb+') as f_ind:
            f_ind.seek(n_links * np.uint32().nbytes - 1)
            f_ind.write(b'\x00')
            f_ind.flush()
            map_ind = mmap.mmap(f_ind.fileno(), 0)
        with map_ind:
            arr_ind = np.frombuffer(map_ind, dtype=np.uint32)
            place_indices(maps, arr_ptr, arr_ind)
