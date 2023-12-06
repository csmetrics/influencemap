"""Utilities for sparse arrays.

The sparse array format is based on the compressed sparse row format.
See https://en.wikipedia.org/wiki/Sparse_matrix#Compressed_sparse_row_(CSR,_CRS_or_Yale_format).

The three differenes are:
1. No value is stored for an array cell.
2. Duplicate entries are permitted.
3. One structure can be used to store multiple maps with the same
   domain by interleaving their data.
"""

import mmap

import numba as nb
import numpy as np
from numba.types import List, Tuple


@nb.njit(nogil=True)
def make_counts(maps, ptr_arr):
    """Count number of edges per index (in the domain) with accumulation.

    In other words, for every input index, ptr_arr[index] is first set
    to the number of elements that index maps to. A cumulative sum is
    then performed over ptr_arr.

    The result tells us the slice of ind_arr that corresponds to every
    index. The elements that index maps to are
    ind_arr[ptr_arr[index-1]:ptr_arr[index]] (note that this is
    slightly different than the final result). This is needed to place
    elements in ind_arr.

    maps is a list of maps. Each map is itself a list of 2-tuples of
    arrays (from index, to index); the to index is ignored here. Within
    each map, the arrays are treated as if they were concatenated. All
    maps must have the same domain, but they don't necessarily have to
    have the same codomain.
    """
    number_maps = len(maps)
    # Account for multiple maps. ptr_arr_2d[domain_index, map_index].
    ptr_arr_2d = ptr_arr[:-1].reshape(-1, number_maps)
    for i, map_ in enumerate(maps):
        map_ptr = ptr_arr_2d[..., i]
        for from_arr, _ in map_:
            # As if all arrays in map_ were concatenated.
            for j in from_arr:
                map_ptr[j] += 1

    cumul = 0
    for i in range(len(ptr_arr)):
        ptr_arr[i] = cumul = ptr_arr[i] + cumul


@nb.njit(nogil=True)
def place_indices(maps, ptr_arr, ind_arr):
    """Place codomain elements in ind_arr.

    In the process, each element of ptr_arr is decremented by the number
    of elements that the corresponding index maps to.
    """
    number_maps = len(maps)
    ptr_arr_2d = ptr_arr[:-1].reshape(-1, number_maps)
    for i, map_ in enumerate(maps):
        map_ptr = ptr_arr_2d[..., i]
        for from_arr, to_arr in map_:
            # Treat all arrays in map_ as concatenated.
            for j, k in zip(from_arr, to_arr):
                # It's not obvious that this gives the correct result,
                # but try it on a piece of paper. map_ptr[j] - 1 is the
                # last free spot. Decrement map_ptr[j] in-place by 1.
                index = map_ptr[j] = map_ptr[j] - 1
                ind_arr[index] = k

    # Sort the image of every index.
    for i in range(len(ptr_arr) - 1):
        start = ptr_arr[i]
        end = ptr_arr[i + 1]
        if end > start + 1:
            ind_arr[start:end].sort()


def make_sparse_matrix(n_from_ind, maps, ptr_path, ind_path):
    """Make sparse matrix representing one of more maps.

    n_from_ind is the number of indices in the domain. maps is a list of
    maps to include in the matrix. ptr_path and ind_path are the
    destinations for the pointer array and the indices array,
    respectively.

    Each map in maps is a list of 2-tuples of NumPy array. This is for
    convenience: each map is treated as the concatenation of all the
    arrays it contains. Each tuple contains a series of domain indices
    and a series of the corresponding codomain indices. They must be of
    the same length and need not be sorted or deduplicated. Separate
    maps are stored separately, but interleaved for locality of
    reference.
    """
    # Convert to types Numba will understand.
    maps = nb.typed.List([
        nb.typed.List([
            (from_series.to_numpy(), to_series.to_numpy())
            for from_series, to_series in map_])
        for map_ in maps])
    n_maps = len(maps)
    n_links = sum(sum(len(s) for s, _ in map_) for map_ in maps)
    with open(ptr_path, 'wb+') as f_ptr:
        # Trick: seek past the end of file and write one byte to
        # efficiently zero-fill up to that point.
        f_ptr.seek((n_maps * n_from_ind + 1) * np.uint64().nbytes - 1)
        f_ptr.write(b'\x00')
        f_ptr.flush()
        map_ptr = mmap.mmap(f_ptr.fileno(), 0)
    with map_ptr:
        arr_ptr = np.frombuffer(map_ptr, dtype=np.uint64)
        make_counts(maps, arr_ptr)
        with open(ind_path, 'wb+') as f_ind:
            # Same trick.
            f_ind.seek(n_links * np.uint64().nbytes - 1)
            f_ind.write(b'\x00')
            f_ind.flush()
            map_ind = mmap.mmap(f_ind.fileno(), 0)
        with map_ind:
            arr_ind = np.frombuffer(map_ind, dtype=np.uint64)
            place_indices(maps, arr_ptr, arr_ind)
