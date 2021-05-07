import pathlib

import numba as nb
import numpy as np

from directed_graph import Graph

ro_f4_arr = nb.types.Array(nb.u4, 1, 'C', readonly=True)


@nb.jit(nb.f4[::1](nb.u4[::1], nb.f4[::1], ro_f4_arr),
        nopython=True, nogil=True)
def _weight_papers(paper_ids, paper_mul, paper_to_author_indptr):
    retval = np.empty_like(paper_mul)
    for i, (id_, mul) in enumerate(zip(paper_ids, paper_mul)):
        num_authors = (paper_to_author_indptr[id_ + 1]
                       - paper_to_author_indptr[id_])
        if num_authors == 0:
            num_authors = 1
        retval[i] = mul / nb.f4(num_authors)
    return retval


class Flower:
    __slots__ = ['influencers', 'influencees']
    def __init__(self, *, influencers=None, influencees=None):
        self.influencers = influencers
        self.influencees = influencees


class Florist:
    def __init__(self, path):
        path = pathlib.Path(path)
        self.author_to_paper = Graph(
            path / 'author2paper-indptr.bin',
            path / 'author2paper-indices.bin',
        )
        self.citee_to_citor = Graph(
            path / 'citee2citor-indptr.bin',
            path / 'citee2citor-indices.bin',
        )
        self.citor_to_citee = Graph(
            path / 'citor2citee-indptr.bin',
            path / 'citor2citee-indices.bin',
        )
        self.paper_to_author = Graph(
            path / 'paper2author-indptr.bin',
            path / 'paper2author-indices.bin',
        )

    def weight_papers(self, papers_with_mul):
        paper_ids, paper_mul = papers_with_mul
        new_mul = _weight_papers(paper_ids, paper_mul,
                                 self.paper_to_author.indptr)
        return paper_ids, new_mul

    def get_flower(self, author_ids):
        origin = np.array(author_ids, dtype=np.uint32)
        origin_papers = self.author_to_paper.traverse(origin)
        weighted_origin_papers = self.weight_papers(origin_papers)

        citing_papers = self.citee_to_citor.traverse(*weighted_origin_papers)
        cited_papers = self.citor_to_citee.traverse(*origin_papers)
        weighted_cited_papers = self.weight_papers(cited_papers)

        influencers = self.paper_to_author.traverse(*weighted_cited_papers)
        influencees = self.paper_to_author.traverse(*citing_papers)
        return Flower(influencers=influencers, influencees=influencees)
