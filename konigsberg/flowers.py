import json
import mmap
import pathlib

import numba as nb
import numpy as np


class Flower:
    __slots__ = ['influencers', 'influencees']
    def __init__(self, *, influencers=None, influencees=None):
        self.influencers = influencers
        self.influencees = influencees


mmapped_arr = nb.types.Array(nb.u4, 1, 'C', readonly=True)
mapping_arrs = nb.types.Tuple([mmapped_arr, mmapped_arr])


@nb.jit(mmapped_arr(mapping_arrs, nb.u4), nopython=True, nogil=True)
def traverse_one(mapping, i):
    indptr, indices = mapping
    start = indptr[i]
    end = indptr[i + 1]
    return indices[start:end]


class Mapping:
    __slots__ = ['indptr', 'indices', 'indptr_mmap', 'indices_mmap']

    def __init__(self, path):
        path = pathlib.Path(path)
        with open(path / 'indptr.bin', 'rb') as f:
            self.indptr_mmap = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        self.indptr = np.frombuffer(self.indptr_mmap, dtype=np.uint32)
        with open(path / 'indices.bin', 'rb') as f:
            self.indices_mmap = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        self.indices = np.frombuffer(self.indices_mmap, dtype=np.uint32)

    def __del__(self):
        self.indptr_mmap.close()
        self.indices_mmap.close()

    @property
    def arrs(self):
        return self.indptr, self.indices


class Florist:
    def __init__(self, path):
        path = pathlib.Path(path)
        self.author2paper = Mapping(path / 'author2paper')
        self.citee2citor = Mapping(path / 'citee2citor')
        self.citor2citee = Mapping(path / 'citor2citee')
        self.paper2author = Mapping(path / 'paper2author')
        with open(path / 'paper-years.json') as f:
            self.year_starts = {
                int(year): start
                for year, start in json.load(f).items()}
        
    def get_id_year_range(self, years):
        if years is None:
            return None

        start_year, end_year = years
        start_id = self.year_starts[start_year]
        end_id = self.year_starts[end_year]
        return nb.u4(start_id), nb.u4(end_id)

    def get_flower(
        self,
        author_ids,
        *,
        self_citations=False, coauthors=True,
        pub_years=None, cit_years=None,
    ):
        pub_ids = self.get_id_year_range(pub_years)
        cit_ids = self.get_id_year_range(cit_years)

        influencers, influencees = _make_flower(
            np.array(author_ids, dtype=np.uint32),
            self.author2paper.arrs, self.paper2author.arrs,
            self.citor2citee.arrs, self.citee2citor.arrs,
            pub_ids, cit_ids,
            nb.types.literal(bool(self_citations)),
            nb.types.literal(bool(coauthors)),
        )
        return Flower(influencers=influencers, influencees=influencees)


@nb.jit(nopython=True, nogil=True)
def _is_self_citation(ego_set, author_ids):
    for author_id in author_ids:
        if author_id in ego_set:
            return True
    return False


@nb.jit(nopython=True, nogil=True)
def _result_dict_to_arr(res):
    ids = np.empty(len(res), dtype=nb.u4)
    scores = np.empty(len(res), dtype=nb.f4)
    for i, (id_, score) in enumerate(res.items()):
        ids[i] = id_
        scores[i] = score
    return ids, scores


@nb.generated_jit(nopython=True, nogil=True)
def _is_in_range(range_, i):
    if isinstance(range_, nb.types.NoneType):
        return lambda range_, i: True
    else:
        return lambda range_, i: range_[0] <= i < range_[1]


@nb.jit(nopython=True, nogil=True)
def _make_flower(
    author_ids,
    author2paper, paper2author, citor2citee, citee2citor,
    pub_ids, cit_ids,
    self_citations, coauthors,
):
    ego_papers = set()
    ego_set = set()
    for author_id in author_ids:
        for paper_id in traverse_one(author2paper, author_id):
            if _is_in_range(pub_ids, paper_id):
                ego_papers.add(paper_id)
        ego_set.add(author_id)

    excluded_authors = ego_set if coauthors else ego_set.copy()
    citor_papers = nb.typed.Dict.empty(key_type=nb.u4, value_type=nb.f4)
    citee_papers = nb.typed.Dict.empty(key_type=nb.u4, value_type=nb.u4)
    for paper_id in ego_papers:
        paper_authors = traverse_one(paper2author, paper_id)
        num_authors = len(paper_authors)
        if not coauthors and num_authors > 1:
            excluded_authors.update(paper_authors)
        recip_weight = nb.f4(1) / nb.f4(num_authors)
        for citor_id in traverse_one(citee2citor, paper_id):
            if _is_in_range(cit_ids, citor_id):
                citor_papers[citor_id] = (
                    citor_papers.get(citor_id, nb.f4(0.)) + recip_weight)
        for citee_id in traverse_one(citor2citee, paper_id):
            if _is_in_range(pub_ids, citee_id):
                citee_papers[citee_id] = nb.u4(
                    citee_papers.get(citee_id, nb.u4(0)) + nb.u4(1))

    citor_authors = nb.typed.Dict.empty(key_type=nb.u4, value_type=nb.f4)
    for paper_id, weight in citor_papers.items():
        author_ids = traverse_one(paper2author, paper_id)
        if not self_citations and _is_self_citation(ego_set, author_ids):
            continue
        for author_id in author_ids:
            if author_id not in excluded_authors:
                citor_authors[author_id] = (
                    citor_authors.get(author_id, nb.f4(0.)) + weight)
    
    citee_authors = nb.typed.Dict.empty(key_type=nb.u4, value_type=nb.f4)
    for paper_id, count in citee_papers.items():
        author_ids = traverse_one(paper2author, paper_id)
        if not self_citations and _is_self_citation(ego_set, author_ids):
            continue
        weight = nb.f4(count) / nb.f4(len(author_ids))
        for author_id in author_ids:
            if author_id not in excluded_authors:
                citee_authors[author_id] = (
                    citee_authors.get(author_id, nb.f4(0.)) + weight)

    return (_result_dict_to_arr(citee_authors),
            _result_dict_to_arr(citor_authors))
