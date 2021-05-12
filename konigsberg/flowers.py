import json
import mmap
import pathlib

import numba as nb
import numpy as np


ID_SENTINEL = nb.u4(0xffffffff)


class Flower:
    __slots__ = ['author_influencers', 'author_influencees',
                 'fos_influencers', 'fos_influencees',
                 'journal_influencers', 'journal_influencees',
                 'conference_series_influencers', 'conference_series_influencees']
    def __init__(
        self,
        *,
        author_influencers=None, author_influencees=None,
        fos_influencers=None, fos_influencees=None,
        journal_influencers=None, journal_influencees=None,
        conference_series_influencers=None, conference_series_influencees=None,
    ):
        self.author_influencers = author_influencers
        self.author_influencees = author_influencees
        self.fos_influencers = fos_influencers
        self.fos_influencees = fos_influencees
        self.journal_influencers = journal_influencers
        self.journal_influencees = journal_influencees
        self.conference_series_influencers = conference_series_influencers
        self.conference_series_influencees = conference_series_influencees


mmapped_arr = nb.types.Array(nb.u4, 1, 'C', readonly=True)
mapping_arrs = nb.types.Tuple([mmapped_arr, mmapped_arr])
mapping_arrs_mask = nb.types.Tuple([mmapped_arr, mmapped_arr, nb.u4])


@nb.njit(mmapped_arr(mapping_arrs, nb.u4), nogil=True)
def traverse_one(mapping, i):
    indptr, indices = mapping
    start = indptr[i]
    end = indptr[i + 1]
    return indices[start:end]


@nb.njit(nb.optional(nb.u4)(mmapped_arr, nb.u4), nogil=True)
def traverse_injective(mapping, i):
    res = mapping[i]
    if res == ID_SENTINEL:
        return None
    return res


@nb.njit(nb.u4(mapping_arrs_mask, nb.u4), nogil=True)
def mag_id_to_id(mapping, mag_id):
    magid2id, id2magid, mask = mapping
    hashed_mag_id = nb.u4(mag_id * nb.u4(0x9e3779b1))
    hashed_mag_id &= mask
    while True:
        candidate_id = magid2id[hashed_mag_id]
        if id2magid[candidate_id] == mag_id:
            return candidate_id
        hashed_mag_id = nb.u4(nb.u4(hashed_mag_id + 1) & mask)


@nb.njit(nb.u4(mapping_arrs_mask, nb.u4), nogil=True)
def id_to_mag_id(mapping, id_):
    magid2id, id2magid, mask = mapping
    return id2magid[id_]


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


class IdMapper:
    __slots__ = ['magid2id', 'id2magid',
                 'magid2id_mmap', 'id2magid_mmap']

    def __init__(self, path):
        path = pathlib.Path(path)
        with open(path / 'id2index.bin', 'rb') as f:
            self.magid2id_mmap = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        self.magid2id = np.frombuffer(self.magid2id_mmap, dtype=np.uint32)
        with open(path / 'index2id.bin', 'rb') as f:
            self.id2magid_mmap = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        self.id2magid = np.frombuffer(self.id2magid_mmap, dtype=np.uint32)

    def __del__(self):
        self.magid2id_mmap.close()
        self.id2magid_mmap.close()

    @property
    def arrs(self):
        mask = nb.u4((1 << (len(self.magid2id).bit_length() - 1)) - 1)
        return self.magid2id, self.id2magid, mask


class InjectiveMapping:
    __slots__ = ['indices', 'indices_mmap']

    def __init__(self, path):
        with open(path, 'rb') as f:
            self.indices_mmap = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        self.indices = np.frombuffer(self.indices_mmap, dtype=np.uint32)

    def __del__(self):
        self.indices_mmap.close()

    @property
    def arrs(self):
        return self.indices


class Florist:
    def __init__(self, path):
        path = pathlib.Path(path)
        self.author2paper = Mapping(path / 'author2paper')
        self.paper2author = Mapping(path / 'paper2author')
        self.fos2paper = Mapping(path / 'fos2paper')
        self.paper2fos = Mapping(path / 'paper2fos')
        self.journal2paper = Mapping(path / 'journal2paper')
        self.paper2journal = InjectiveMapping(path / 'paper2journal.bin')
        self.cs2paper = Mapping(path / 'cs2paper')
        self.paper2cs = InjectiveMapping(path / 'paper2cs.bin')
        self.citor2citee = Mapping(path / 'citor2citee')
        self.citee2citor = Mapping(path / 'citee2citor')
        self.author_magid2id = IdMapper(path / 'author-id-map')
        self.fos_magid2id = IdMapper(path / 'field-of-study-id-map')
        self.journal_magid2id = IdMapper(path / 'journal-id-map')
        self.cs_magid2id = IdMapper(path / 'conference-series-id-map')
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
        *,
        author_ids=(),
        fos_ids=(),
        self_citations=False, coauthors=True,
        pub_years=None, cit_years=None,
    ):
        pub_ids = self.get_id_year_range(pub_years)
        cit_ids = self.get_id_year_range(cit_years)

        (author_influencers, author_influencees,
         fos_influencers, fos_influencees) = _make_flower(
            np.array(author_ids, dtype=np.uint32),
            np.array(fos_ids, dtype=np.uint32),
            self.author_magid2id.arrs,
            self.fos_magid2id.arrs,
            self.journal_magid2id.arrs,
            self.cs_magid2id.arrs,
            self.author2paper.arrs, self.paper2author.arrs,
            self.fos2paper.arrs, self.paper2fos.arrs,
            self.journal2paper.arrs, self.paper2journal.arrs,
            self.cs2paper.arrs, self.paper2cs.arrs,
            self.citor2citee.arrs, self.citee2citor.arrs,
            pub_ids, cit_ids,
            nb.types.literal(bool(self_citations)),
            nb.types.literal(bool(coauthors)),
        )
        return Flower(
            author_influencers=author_influencers,
            author_influencees=author_influencees,
            fos_influencers=fos_influencers,
            fos_influencees=fos_influencees,
            journal_influencers=journal_influencers,
            journal_influencees=journal_influencees,
            conference_series_influencers=conference_series_influencers,
            conference_series_influencees=conference_series_influencees)


@nb.njit(nogil=True)
def _is_self_citation(
    ego_author_set, author_ids, ego_fos_set, fos_ids,
    ego_journals_set, journal_id_or_none, ego_cs_set, cs_id_or_none,
):
    for author_id in author_ids:
        if author_id in ego_author_set:
            return True
    for fos_id in fos_ids:
        if fos_id in ego_fos_set:
            return True
    if journal_id_or_none is not None:
        if journal_id_or_none in ego_journals_set:
            return True
    if cs_id_or_none is not None:
        if cs_id_or_none in ego_cs_set:
            return True
    return False


@nb.njit(nogil=True)
def _result_dict_to_arr(res, author_magid2id):
    ids = np.empty(len(res), dtype=nb.u4)
    scores = np.empty(len(res), dtype=nb.f4)
    for i, (id_, score) in enumerate(res.items()):
        ids[i] = id_to_mag_id(author_magid2id, id_)
        scores[i] = score
    return ids, scores


@nb.generated_jit(nopython=True, nogil=True)
def _is_in_range(range_, i):
    if isinstance(range_, nb.types.NoneType):
        return lambda range_, i: True
    else:
        return lambda range_, i: range_[0] <= i < range_[1]


dict_val = nb.types.Tuple([nb.u4, nb.f4])


@nb.njit(nogil=True)
def _make_flower(
    mag_author_ids, mag_fos_ids, mag_journal_ids, mag_cs_ids,
    author_magid2id, fos_magid2id, journal_magid2id, cs_magid2id,
    author2paper, paper2author, fos2paper, paper2fos,
    journal2paper, paper2journal, cs2paper, paper2cs,
    citor2citee, citee2citor,
    pub_ids, cit_ids,
    self_citations, coauthors,
):
    ego_papers = set()
    ego_authors_set = set()
    ego_fos_set = set()
    ego_journals_set = set()
    ego_cs_set = set()

    for mag_author_id in mag_author_ids:
        author_id = mag_id_to_id(author_magid2id, mag_author_id)
        for paper_id in traverse_one(author2paper, author_id):
            if _is_in_range(pub_ids, paper_id):
                ego_papers.add(paper_id)
        ego_authors_set.add(author_id)

    for mag_fos_id in mag_fos_ids:
        fos_id = mag_id_to_id(fos_magid2id, mag_fos_id)
        for paper_id in traverse_one(fos2paper, fos_id):
            if _is_in_range(pub_ids, paper_id):
                ego_papers.add(paper_id)
        ego_fos_set.add(fos_id)

    for mag_journal_id in mag_journal_ids:
        journal_id = mag_id_to_id(journal_magid2id, mag_journal_id)
        for paper_id in traverse_one(journal2paper, journal_id):
            if _is_in_range(pub_ids, paper_id):
                ego_papers.add(paper_id)
        ego_journals_set.add(journal_id)

    for mag_cs_id in mag_cs_ids:
        cs_id = mag_id_to_id(cs_magid2id, mag_cs_id)
        for paper_id in traverse_one(cs2paper, cs_id):
            if _is_in_range(pub_ids, paper_id):
                ego_papers.add(paper_id)
        ego_cs_set.add(cs_id)

    excluded_authors = ego_authors_set if coauthors else ego_authors_set.copy()
    excluded_fos = ego_fos_set if coauthors else ego_fos_set.copy()
    excluded_journals = ego_journals_set if cojournals else ego_journals_set.copy()
    excluded_cs = ego_cs_set if coauthors else ego_cs_set.copy()
    citor_papers = nb.typed.Dict.empty(key_type=nb.u4, value_type=dict_val)
    citee_papers = nb.typed.Dict.empty(key_type=nb.u4, value_type=nb.u4)
    for paper_id in ego_papers:
        paper_authors = traverse_one(paper2author, paper_id)
        num_authors = max(len(paper_authors), 1)
        if not coauthors:
            excluded_authors.update(paper_authors)
            excluded_fos.update(traverse_one(paper2fos, paper_id))
            journal_id_or_none = traverse_injective(paper2journal, paper_id)
            if journal_id_or_none is not None:
                excluded_journals.add(journal_id_or_none)
            cs_id_or_none = traverse_injective(paper2cs, paper_id)
            if cs_id_or_none is not None:
                excluded_cs.add(cs_id_or_none)
        recip_weight = nb.f4(1) / nb.f4(num_authors)
        for citor_id in traverse_one(citee2citor, paper_id):
            if _is_in_range(cit_ids, citor_id):
                curr_count, curr_score = citor_papers.get(
                    citor_id, (nb.u4(0), nb.f4(0.)))
                new_count = curr_count + 1
                new_score = curr_score + recip_weight
                citor_papers[citor_id] = new_count, new_score
        for citee_id in traverse_one(citor2citee, paper_id):
            if _is_in_range(pub_ids, citee_id):
                citee_papers[citee_id] = nb.u4(
                    citee_papers.get(citee_id, nb.u4(0)) + nb.u4(1))

    citor_authors = nb.typed.Dict.empty(key_type=nb.u4, value_type=nb.f4)
    citor_fos = nb.typed.Dict.empty(key_type=nb.u4, value_type=nb.f4)
    citor_journals = nb.typed.Dict.empty(key_type=nb.u4, value_type=nb.f4)
    citor_cs = nb.typed.Dict.empty(key_type=nb.u4, value_type=nb.f4)
    for paper_id, (count, weight) in citor_papers.items():
        author_ids = traverse_one(paper2author, paper_id)
        fos_ids = traverse_one(paper2fos, paper_id)
        journal_id_or_none = traverse_injective(paper2journal, paper_id)
        cs_id_or_none = traverse_injective(paper2cs, paper_id)
        if not self_citations and _is_self_citation(
                ego_authors_set, author_ids, ego_fos_set, fos_ids,
                ego_journals_set, journal_id_or_none,
                ego_cs_set, cs_id_or_none):
            continue
        for author_id in author_ids:
            if author_id not in excluded_authors:
                citor_authors[author_id] = (
                    citor_authors.get(author_id, nb.f4(0.)) + weight)
        for fos_id in fos_ids:
            if fos_id not in excluded_fos:
                citor_fos[fos_id] = (
                    citor_fos.get(fos_id, nb.f4(0.)) + nb.f4(count))
        if journal_id_or_none is not None:
            if journal_id_or_none not in excluded_journals:
                citor_journals[journal_id_or_none] = (
                    citor_journals.get(journal_id_or_none, nb.f4(0.))
                    + nb.f4(count))
        if cs_id_or_none is not None:
            if cs_id_or_none not in excluded_cs:
                citor_cs[cs_id_or_none] \
                    = citor_cs.get(cs_id_or_none, nb.f4(0.)) + nb.f4(count)

    
    citee_authors = nb.typed.Dict.empty(key_type=nb.u4, value_type=nb.f4)
    citee_fos = nb.typed.Dict.empty(key_type=nb.u4, value_type=nb.f4)
    citee_journals = nb.typed.Dict.empty(key_type=nb.u4, value_type=nb.f4)
    citee_cs = nb.typed.Dict.empty(key_type=nb.u4, value_type=nb.f4)
    for paper_id, count in citee_papers.items():
        author_ids = traverse_one(paper2author, paper_id)
        fos_ids = traverse_one(paper2fos, paper_id)
        journal_id_or_none = traverse_injective(paper2journal, paper_id)
        cs_id_or_none = traverse_injective(paper2cs, paper_id)
        if not self_citations and _is_self_citation(
                ego_authors_set, author_ids, ego_fos_set, fos_ids,
                ego_journals_set, journal_id_or_none,
                ego_cs_set, cs_id_or_none):
            continue
        weight = nb.f4(count) / nb.f4(max(len(author_ids), 1))
        for author_id in author_ids:
            if author_id not in excluded_authors:
                citee_authors[author_id] = (
                    citee_authors.get(author_id, nb.f4(0.)) + weight)
        for fos_id in fos_ids:
            if fos_id not in excluded_fos:
                citee_fos[fos_id] = (
                    citee_fos.get(fos_id, nb.f4(0.)) + nb.f4(count))
        if journal_id_or_none is not None:
            if journal_id_or_none not in excluded_journals:
                citee_journals[journal_id_or_none] = (
                    citee_journals.get(journal_id_or_none, nb.f4(0.))
                    + nb.f4(count))
        if cs_id_or_none is not None:
            if cs_id_or_none not in excluded_cs:
                citee_cs[cs_id_or_none] \
                    = citee_cs.get(cs_id_or_none, nb.f4(0.)) + nb.f4(count)

    return (_result_dict_to_arr(citee_authors, author_magid2id),
            _result_dict_to_arr(citor_authors, author_magid2id),
            _result_dict_to_arr(citee_fos, fos_magid2id),
            _result_dict_to_arr(citor_fos, fos_magid2id),
            _result_dict_to_arr(citee_journals, journal_magid2id),
            _result_dict_to_arr(citor_journals, journal_magid2id),
            _result_dict_to_arr(citee_cs, cs_magid2id),
            _result_dict_to_arr(citor_cs, cs_magid2id))
