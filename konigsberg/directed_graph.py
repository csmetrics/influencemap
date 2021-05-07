import mmap

import numba as nb
import numpy as np


ro_array = nb.types.Array(nb.u4, 1, 'C', readonly=True)

@nb.jit(nb.u4[::1](ro_array, ro_array, nb.u4[::1]),
        nopython=True, nogil=True)
def traverse(indptr, indices, origins):
    sinks = set()
    for vo in origins:
        start = indptr[vo]
        end = indptr[vo + 1]
        sinks.update(indices[start:end])
    res = np.empty(len(sinks), dtype=np.uint32)
    for i, s in enumerate(sinks):
        res[i] = s
    return res


class Graph:
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


class InfluenceeGetter:
    def __init__(self, path):
        self.author_to_paper = Graph(
            path / 'author2paper-indptr.bin',
            path / 'author2paper-indices.bin',
        )
        self.citee_to_citor = Graph(
            path / 'citee2citor-indptr.bin',
            path / 'citee2citor-indices.bin',
        )
        self.paper_to_author = Graph(
            path / 'paper2author-indptr.bin',
            path / 'paper2author-indices.bin',
        )

    def get_influencees(self, author_id):
        origin = np.array([author_id], dtype=np.uint32)
        papers = traverse(self.author_to_paper.indptr,
                          self.author_to_paper.indices, origin)
        citing_papers = traverse(self.citee_to_citor.indptr,
                                 self.citee_to_citor.indices, papers)
        influencees = traverse(self.paper_to_author.indptr,
                               self.paper_to_author.indices, citing_papers)
        return influencees
