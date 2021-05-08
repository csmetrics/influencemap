import json
import pathlib

import numba as nb
import numpy as np

from directed_graph import Graph

ro_u4_arr = nb.types.Array(nb.u4, 1, 'C', readonly=True)


@nb.jit(nb.f4[::1](nb.u4[::1], nb.f4[::1], ro_u4_arr),
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


@nb.jit(nb.types.Tuple([nb.u4[::1], nb.f4[::1]])(
            nb.u4[::1], nb.u4[::1], nb.f4[::1], ro_u4_arr, ro_u4_arr),
        nopython=True, nogil=True)
def _filter_self_citations(
    author_ids,
    paper_ids, paper_muls,
    paper_to_author_indptr, paper_to_author_indices
):
    new_paper_ids = []
    new_paper_muls = []
    for paper_id, paper_mul in zip(paper_ids, paper_muls):
        start = paper_to_author_indptr[paper_id]
        end = paper_to_author_indptr[paper_id + 1]
        # Below equivalent to:
        #     if not any(any(author_id == other_author_id
        #                    for other_author_id
        #                        in paper_to_author_indices[start:end])
        #                for author_id in author_ids):
        for author_id in author_ids:
            if author_id in paper_to_author_indices[start:end]:
                break
        else:
            new_paper_ids.append(paper_id)
            new_paper_muls.append(paper_mul)
    return np.array(new_paper_ids), np.array(new_paper_muls)


@nb.jit(nb.types.Tuple([nb.u4[::1], nb.f4[::1]])(
            nb.u4[::1], nb.u4[::1], nb.f4[::1]),
        nopython=True, nogil=True)
def _filter_ego(
    author_ids_ego,
    author_ids_other, author_muls_other,
):
    new_author_ids_other = []
    new_author_muls_other = []
    for author_id, author_mul in zip(author_ids_other, author_muls_other):
        if author_id not in author_ids_ego:
            new_author_ids_other.append(author_id)
            new_author_muls_other.append(author_mul)
    return np.array(new_author_ids_other), np.array(new_author_muls_other)


@nb.jit(nb.types.Tuple([nb.u4[::1], nb.f4[::1]])(
            nb.u4[::1], nb.u4[::1], nb.f4[::1], ro_u4_arr, ro_u4_arr),
        nopython=True, nogil=True)
def _filter_coauthors(
    ego_paper_ids,
    author_ids_other, author_muls_other,
    p2a_ptr, p2a_idx,
):
    coauthors = set()
    for paper_id in ego_paper_ids:
        start = p2a_ptr[paper_id]
        end = p2a_ptr[paper_id + 1]
        coauthors.update(p2a_idx[start:end])

    new_author_ids_other = []
    new_author_muls_other = []
    for author_id, author_mul in zip(author_ids_other, author_muls_other):
        if author_id not in coauthors:
            new_author_ids_other.append(author_id)
            new_author_muls_other.append(author_mul)

    return np.array(new_author_ids_other), np.array(new_author_muls_other)


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
        with open(path / 'paper-years.json') as f:
            data = json.load(f)
        self.year_starts = {int(year): start for year, start in data.items()}

    def weight_papers(self, papers_with_mul):
        paper_ids, paper_mul = papers_with_mul
        new_mul = _weight_papers(paper_ids, paper_mul,
                                 self.paper_to_author.indptr)
        return paper_ids, new_mul

    def filter_self_citations(self, author_ids, papers_with_mul):
        paper_ids, paper_muls = papers_with_mul
        return _filter_self_citations(
            author_ids,
            paper_ids, paper_muls,
            self.paper_to_author.indptr, self.paper_to_author.indices)
        
    def get_id_year_range(self, start, end):
        return self.year_starts.get(start), self.year_starts.get(end)

    def get_flower(
        self,
        author_ids,
        *,
        self_citations=False,
        coauthors=True,
        pub_year_start=None, pub_year_end=None,
        cit_year_start=None, cit_year_end=None,
    ):
        pub_year_start, pub_year_end = self.get_id_year_range(
            pub_year_start, pub_year_end)
        cit_year_start, cit_year_end = self.get_id_year_range(
            cit_year_start, cit_year_end)

        origin = np.array(author_ids, dtype=np.uint32)
        origin_papers = self.author_to_paper.traverse(
            origin, id_start=pub_year_start, id_end=pub_year_end)
        origin_papers = origin_papers[0], np.ones_like(origin_papers[1])
        weighted_origin_papers = self.weight_papers(origin_papers)

        citing_papers = self.citee_to_citor.traverse(
            *weighted_origin_papers,
            id_start=cit_year_start, id_end=cit_year_end)
        if not self_citations:
            citing_papers = self.filter_self_citations(origin, citing_papers)
        cited_papers = self.citor_to_citee.traverse(
            *origin_papers, id_start=pub_year_start, id_end=pub_year_end)
        if not self_citations:
            cited_papers = self.filter_self_citations(origin, cited_papers)
        weighted_cited_papers = self.weight_papers(cited_papers)

        influencers = self.paper_to_author.traverse(*weighted_cited_papers)
        if coauthors:
            influencers = _filter_ego(origin, *influencers)
        else:
            influencers = _filter_coauthors(
                origin_papers[0],
                influencers[0], influencers[1],
                self.paper_to_author.indptr, self.paper_to_author.indices)
        influencees = self.paper_to_author.traverse(*citing_papers)
        if coauthors:
            influencees = _filter_ego(origin, *influencees)
        else:
            influencees = _filter_coauthors(
                origin_papers[0],
                influencees[0], influencees[1],
                self.paper_to_author.indptr, self.paper_to_author.indices)
        return Flower(influencers=influencers, influencees=influencees)
