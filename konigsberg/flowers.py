import heapq
import itertools
import json
import mmap
import operator
import pathlib
from itertools import chain, starmap

import numba as nb
import numpy as np

mmapped_arr = nb.types.Array(nb.u4, 1, 'C', readonly=True)
mapping_arrs = nb.types.Tuple([mmapped_arr, mmapped_arr])
id_mapping_arrs = nb.types.Tuple([mmapped_arr, mmapped_arr, nb.u4])


class Subflower:
    __slots__ = ['ids', 'citor_scores', 'citee_scores', 'coauthors',
                 'kinds', 'total']
    def __init__(
            self, ids, citor_scores, citee_scores, coauthors, kinds, total):
        self.ids = ids
        self.citor_scores = citor_scores
        self.citee_scores = citee_scores
        self.coauthors = coauthors
        self.kinds = kinds
        self.total = total


class Flower:
    """Full result."""
    __slots__ = ['author', 'affiliation', 'field_of_study', 'venue']

    def __init__(
        self,
        *,
        author, affiliation, field_of_study, venue,
    ):
        self.author = author
        self.affiliation = affiliation
        self.field_of_study = field_of_study
        self.venue = venue


class Stats:
    __slots__ = ['pub_year_counts', 'cit_year_counts', 'pub_count',
                 'cit_count', 'ref_count']

    def __init__(
        self,
        *,
        pub_year_counts, cit_year_counts, pub_count, cit_count, ref_count,
    ):
        self.pub_year_counts = pub_year_counts
        self.cit_year_counts = cit_year_counts
        self.pub_count = pub_count
        self.cit_count = cit_count
        self.ref_count = ref_count


class Mapping:
    """Pair of memory-mapped arrays representing a mapping."""
    __slots__ = ['ptr', 'ind', 'ptr_mmap', 'ind_mmap']

    def __init__(self, ptr_path, ind_path):
        """Initialize from files."""
        with open(ptr_path, 'rb') as f:
            self.ptr_mmap = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        self.ptr = np.frombuffer(self.ptr_mmap, dtype=np.uint64)
        with open(ind_path, 'rb') as f:
            self.ind_mmap = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        self.ind = np.frombuffer(self.ind_mmap, dtype=np.uint64)

    def __del__(self):
        self.ptr_mmap.close()
        self.ind_mmap.close()

    @property
    def arrs(self):
        """Get contents as a tuple."""
        return self.ptr, self.ind


class IndToIdMapper:
    """Memory-mapped array mapping indices to MAG IDs."""
    __slots__ = ['ind2id_mmap', 'ind2id']

    def __init__(self, ind2id_path):
        with open(ind2id_path, 'rb') as f:
            self.ind2id_mmap = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        self.ind2id = np.frombuffer(self.ind2id_mmap, dtype=np.uint64)

    def __del__(self):
        self.ind2id_mmap.close()

    @property
    def arrs(self):
        return self.ind2id


class IdToIndMapper:
    """Memory-mapped hash table mapping MAG IDs to indices."""
    __slots__ = ['id2ind_mmap', 'id2ind', 'ind2id_mapper']

    def __init__(self, id2ind_path, ind2id_mapper):
        with open(id2ind_path, 'rb') as f:
            self.id2ind_mmap = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        self.id2ind = np.frombuffer(self.id2ind_mmap, dtype=np.uint64)
        self.ind2id_mapper = ind2id_mapper

    def __del__(self):
        self.id2ind_mmap.close()

    @property
    def arrs(self):
        mask = nb.u4(len(self.id2ind) - 1)
        return self.id2ind, self.ind2id_mapper.arrs, mask


class Florist:
    """Makes flowers."""

    def __init__(self, path):
        """Initialize from files written by the builder to path."""
        path = pathlib.Path(path)
        self.entity2paper_map = Mapping(path / 'entity2paper-ptr.bin',
                                        path / 'entity2paper-ind.bin')
        self.paper2entity_map = Mapping(path / 'paper2entity-ptr.bin',
                                        path / 'paper2entity-ind.bin')
        self.citation_maps = Mapping(path / 'paper2citor-citee-ptr.bin',
                                     path / 'paper2citor-citee-ind.bin')
        self.entity_ind2id_map = IndToIdMapper(path / 'entities-ind2id.bin')
        self.author_id2ind_map = IdToIndMapper(
            path / 'author-id2ind.bin', self.entity_ind2id_map)
        self.aff_id2ind_map = IdToIndMapper(
            path / 'affltn-id2ind.bin', self.entity_ind2id_map)
        self.fos_id2ind_map = IdToIndMapper(
            path / 'fos-id2ind.bin', self.entity_ind2id_map)
        self.journal_id2ind_map = IdToIndMapper(
            path / 'journl-id2ind.bin', self.entity_ind2id_map)
        self.cs_id2ind_map = IdToIndMapper(
            path / 'cs-id2ind.bin', self.entity_ind2id_map)

        self.paper_ind2id_map = IndToIdMapper(path / 'paper-ind2id.bin')
        self.paper_id2ind_map = IdToIndMapper(
            path / 'paper-id2ind.bin', self.paper_ind2id_map)

        with open(path / 'paper-years.json') as f:
            # Maps year (int) to the index of the first paper published
            # that year. Since the papers are sorted in chronological
            # order, this is used for filtering.
            self.year_starts = {
                int(year): start
                for year, start in json.load(f).items()}
        paper_year_map = [self.year_starts[year]
                          for year in sorted(self.year_starts)]
        self.paper_year_map = np.array(paper_year_map, dtype=np.uint64)
        with open(path / 'entity-counts.json') as f:
            # Distinguish entity types, i.e., author, affiliation,
            # conference series, journal, and field of study.
            entity_counts_data = json.load(f)
        self.author_range = entity_counts_data['authors']
        self.aff_range = self.author_range + entity_counts_data['aff']
        self.fos_range = self.aff_range + entity_counts_data['fos']
        self.journal_range = self.fos_range + entity_counts_data['journals']
        self.cs_range = self.journal_range + entity_counts_data['cs']
        with open(path / 'fos-meta.json') as f:
            fos_meta = json.load(f)
        self.fos_l1_start = self.aff_range + fos_meta['level0count']

    def _get_id_year_range(self, years):
        """Get range of paper indices corresponding to a range of years.

        years is None or a 2-tuple of ints. Returns a 2-tuple of Numpy
        uint64s.
        """
        if years is None:
            return None
        start_year, end_year = years
        start_id = self.year_starts[start_year]
        end_id = self.year_starts[end_year]
        return nb.u4(start_id), nb.u4(end_id)

    def _ids_to_indices(self, ids, mapper, allow_not_found):
        """Convert IDs to indices."""
        indices = np.array(ids, dtype=np.uint64)
        length = _ids_to_ind(mapper.arrs, indices)
        if not allow_not_found and length < len(indices):
            raise KeyError('id not found')
        return indices[:length]

    def _id_to_index(self, type, id, allow_not_found):
        in2ind_maps = [
            self.author_id2ind_map,
            self.journal_id2ind_map,
            self.aff_id2ind_map,
            self.fos_id2ind_map
        ]
        # There should be better way to find whether it is journal or conference type
        if type == 1:
            try:
                index = self._ids_to_indices(
                    [id], self.journal_id2ind_map, allow_not_found)[0]
            except:
                index = self._ids_to_indices(
                    [id], self.cs_id2ind_map, allow_not_found)[0]
        else:
            index = self._ids_to_indices(
                [id], in2ind_maps[type], allow_not_found)[0]
        return index

    def _get_entity_indices(
        self,
        *,
        author_ids, aff_ids, fos_ids, journal_ids, cs_ids, allow_not_found
    ):
        """Convert IDs to indices and concatenate."""
        author_indices = self._ids_to_indices(
            author_ids, self.author_id2ind_map, allow_not_found)
        aff_indices = self._ids_to_indices(
            aff_ids, self.aff_id2ind_map, allow_not_found)
        fos_indices = self._ids_to_indices(
            fos_ids, self.fos_id2ind_map, allow_not_found)
        journal_indices = self._ids_to_indices(
            journal_ids, self.journal_id2ind_map, allow_not_found)
        cs_indices = self._ids_to_indices(
            cs_ids, self.cs_id2ind_map, allow_not_found)
        return np.concatenate([author_indices, aff_indices, fos_indices,
                               journal_indices, cs_indices])

    def _get_paper_indices(self, paper_ids, *, allow_not_found):
        return self._ids_to_indices(
            paper_ids, self.paper_id2ind_map, allow_not_found)

    def _make_pub_year_count_dict(self, pub_year_counts):
        min_year = min(self.year_starts)
        return {
            year: count
            for year, count in enumerate(map(int, pub_year_counts[:-1]),
                                         start=min_year)
            if count
        }

    def _make_cit_year_count_dict(self, cit_year_counts):
        min_year = min(self.year_starts)
        return {
            year: {
                year_: count
                for year_, count in enumerate(map(int, row[:-1]),
                                              start=min_year)
                if count
            }
            for year, row in enumerate(cit_year_counts[:-1], start=min_year)
            if row[:-1].any()
        }

    def _make_flower_from_res(self, raw_result, max_results):
        split_res = get_split_res(
            raw_result, self.author_range, self.aff_range, self.fos_range,
            self.journal_range, self.cs_range, self.fos_l1_start)

        author_tot, aff_tot, fos_tot, venue_tot = map(len, split_res)

        if max_results is None:
            for kind_res in split_res:
                _sort(kind_res)
        else:
            for kind_res in split_res:
                _select_top_n(kind_res, max_results)

        for kind_res in split_res:
            _indices_to_ids(kind_res, self.entity_ind2id_map.arrs)

        author_res, aff_res, fos_res, venue_res = split_res

        author_flwr = Subflower(*_to_arrs(author_res), author_tot)
        aff_flwr = Subflower(*_to_arrs(aff_res), aff_tot)
        fos_flwr = Subflower(*_to_arrs(fos_res), fos_tot)
        venue_flwr = Subflower(*_to_arrs(venue_res), venue_tot)

        return Flower(author=author_flwr, affiliation=aff_flwr,
                      field_of_study=fos_flwr, venue=venue_flwr)

    def _make_stats_from_arrs(
        self,
        pub_year_counts, cit_year_counts, ref_count,
    ):
        pub_year_count_dict = self._make_pub_year_count_dict(pub_year_counts)
        cit_year_count_dict = self._make_cit_year_count_dict(cit_year_counts)
        pub_count = np.sum(pub_year_counts)
        cit_count = np.sum(cit_year_counts)

        return Stats(pub_year_counts=pub_year_count_dict,
                     cit_year_counts=cit_year_count_dict,
                     pub_count=int(pub_count),
                     cit_count=int(cit_count),
                     ref_count=int(ref_count))

    def get_flower(
        self,
        *,
        author_ids=[],
        affiliation_ids=[],
        field_of_study_ids=[],
        journal_ids=[],
        conference_series_ids=[],
        paper_ids=[],
        self_citations=False, coauthors=True,
        pub_years=None, cit_years=None,
        allow_not_found=False,
        max_results=None,
    ):
        """Get the flower for the given entity indices.

        If self_citations=True, self_citations are not filtered out
        (default False). If coauthors=False, coauthors are filtered out
        (default True). If pub_years is provided, it must be a 2-tuple
        of integers (start, end), representing the range of years to
        search; start is inclusive, and end is exclusive. cit_years is
        the same for citation years.

        Returns a 2-tuple of dictionaries (influencers, influencees)
        mapping the entity index to their score.
        """
        # TODO: if coauthors=False, self_citations has no effect on the
        # result, but may affect the speed of the computation. Figure
        # out whether it's faster to include or exclude them and set it
        # to that.

        entity_indices = self._get_entity_indices(
            author_ids=author_ids, aff_ids=affiliation_ids,
            fos_ids=field_of_study_ids, journal_ids=journal_ids,
            cs_ids=conference_series_ids, allow_not_found=allow_not_found)
        paper_indices = self._get_paper_indices(
            paper_ids, allow_not_found=allow_not_found)

        pub_ids = self._get_id_year_range(pub_years)
        cit_ids = self._get_id_year_range(cit_years)

        # nb.literally makes it a compile-time constant. This does
        # require one compilation per value.
        raw_result = _make_flower(
            entity_indices, paper_indices,
            self.entity2paper_map.arrs,
            self.paper2entity_map.arrs,
            self.citation_maps.arrs,
            pub_ids=pub_ids, cit_ids=cit_ids,
            self_citations=nb.literally(bool(self_citations)),
            coauthors=nb.literally(bool(coauthors)),
            author_range=nb.literally(self.author_range),
            aff_range=nb.literally(self.aff_range))
        return self._make_flower_from_res(raw_result, max_results)

    def get_stats(
        self,
        *,
        author_ids=[],
        affiliation_ids=[],
        field_of_study_ids=[],
        journal_ids=[],
        conference_series_ids=[],
        paper_ids=[],
        allow_not_found=False,
    ):
        entity_indices = self._get_entity_indices(
            author_ids=author_ids, aff_ids=affiliation_ids,
            fos_ids=field_of_study_ids, journal_ids=journal_ids,
            cs_ids=conference_series_ids, allow_not_found=allow_not_found)
        paper_indices = self._get_paper_indices(
            paper_ids, allow_not_found=allow_not_found)

        pub_year_counts, cit_year_counts, ref_count = _make_stats(
            entity_indices, paper_indices,
            self.entity2paper_map.arrs,
            self.citation_maps.arrs,
            paper_year_map=self.paper_year_map)
        return self._make_stats_from_arrs(
            pub_year_counts, cit_year_counts, ref_count)

    def get_node_info(
        self,
        *,
        node_id=None,
        node_type=None,
        author_ids=[],
        affiliation_ids=[],
        field_of_study_ids=[],
        journal_ids=[],
        conference_series_ids=[],
        paper_ids=[],
        self_citations=False, coauthors=True,
        pub_years=None, cit_years=None,
        allow_not_found=False,
        max_results=None,
    ):
        """Get the list of papers between the given entity and the ego.

        Returns a 2-tuple of dictionaries (influencers, influencees)
        of the paper indices.
        """
        # TODO: if coauthors=False, self_citations has no effect on the
        # result, but may affect the speed of the computation. Figure
        # out whether it's faster to include or exclude them and set it
        # to that.

        # convert node_id to node_index.
        node_index = self._id_to_index(
            type=node_type, id=node_id, allow_not_found=allow_not_found)

        entity_indices = self._get_entity_indices(
            author_ids=author_ids, aff_ids=affiliation_ids,
            fos_ids=field_of_study_ids, journal_ids=journal_ids,
            cs_ids=conference_series_ids, allow_not_found=allow_not_found)
        paper_indices = self._get_paper_indices(
            paper_ids, allow_not_found=allow_not_found)

        pub_ids = self._get_id_year_range(pub_years)
        cit_ids = self._get_id_year_range(cit_years)

        # nb.literally makes it a compile-time constant. This does
        # require one compilation per value.
        citor_papers, citee_papers = _make_node_info(
            node_index,
            entity_indices, paper_indices,
            self.entity2paper_map.arrs,
            self.paper2entity_map.arrs,
            self.citation_maps.arrs,
            pub_ids=pub_ids, cit_ids=cit_ids,
            self_citations=nb.literally(bool(self_citations)),
            coauthors=nb.literally(bool(coauthors)),
            author_range=nb.literally(self.author_range),
            aff_range=nb.literally(self.aff_range))

        # convert paper indices to paper ids
        # return [int(self.paper_ind2id_map.arrs[idx]) for idx in citor_papers]
        return _summarize_node_info(citor_papers, citee_papers, self.paper_ind2id_map.arrs)


def _summarize_node_info(citor_papers, citee_papers, ind2id):
    node_info = {}
    for citee_idx, paper_idx in citee_papers:
        paper_id = str(ind2id[paper_idx])
        citee_id = str(ind2id[citee_idx])
        if citee_id not in node_info:
            node_info[citee_id] = {"reference": [], "citation": []}
        node_info[citee_id]["citation"].append(paper_id)
    for paper_idx, citor_idx in citor_papers:
        paper_id = str(ind2id[paper_idx])
        citor_id = str(ind2id[citor_idx])
        if citor_id not in node_info:
            node_info[citor_id] = {"reference": [], "citation": []}
        node_info[citor_id]["reference"].append(paper_id)
    return node_info


split_result_val_t = nb.types.Tuple([nb.u4, nb.f4, nb.f4, nb.u1, nb.u1])


@nb.njit(nogil=True)
def get_split_res(
    res,
    author_range, aff_range, fos_range, journal_range, cs_range,
    fos_l1_start,
):
    """Split a dict of indices and scores by entity type."""
    author_res = nb.typed.List.empty_list(split_result_val_t)
    aff_res = nb.typed.List.empty_list(split_result_val_t)
    fos_res = nb.typed.List.empty_list(split_result_val_t)
    venues_res = nb.typed.List.empty_list(split_result_val_t)
    for index, citor_score, citee_score, coauthor in res:
        if index < author_range:
            author_res.append(
                (index, citor_score, citee_score, coauthor, nb.u1(0)))
        elif index < aff_range:
            aff_res.append(
                (index, citor_score, citee_score, coauthor, nb.u1(1)))
        elif index < fos_l1_start:
            pass  # Skip l0 fields of study.
        elif index < fos_range:
            fos_res.append(
                (index, citor_score, citee_score, coauthor, nb.u1(3)))
        elif index < cs_range:
            venues_res.append((index, citor_score, citee_score, coauthor,
                               nb.u1(4 if index < journal_range else 2)))
        else:
            raise IndexError('entity index out of range')
    return author_res, aff_res, fos_res, venues_res


@nb.njit(nogil=True)
def _sort(res_list):
    res_list.sort(key=lambda r: (-max(r[1], r[2]), -r[1] - r[2], r[0]))


@nb.njit(nogil=True)
def _select_top_n(res_list, max_results):
    # if len(res_list) > max_results:
    #     smallest = heapq.nsmallest(
    #         max_results,
    #         map(lambda r, i: (-max(r[1], r[2]), -r[1] - r[2],
    #                        r[0], i),
    #             res_list, itertools.count()))
    #     indices = sorted(map(operator.itemgetter(3), smallest))
    #     for i, j in enumerate(indices):
    #         # i <= j at all times
    #         res_list[i] = res_list[j]
    #     del res_list[max_results:]
    # res_list.sort(key=lambda r: (-max(r[1], r[2]), -r[1] - r[2], r[0]))
    res_list.sort(key=lambda r: (-max(r[1], r[2]), -r[1] - r[2], r[0]))
    if len(res_list) > max_results:
        del res_list[max_results:]


@nb.njit(nogil=True)
def _to_arrs(res_list):
    n = len(res_list)
    id_arr = np.empty(n, dtype=np.uint64)
    citor_score_arr = np.empty(n, dtype=np.float32)
    citee_score_arr = np.empty(n, dtype=np.float32)
    coauthor_arr = np.empty(n, dtype=np.uint8)
    kind_arr = np.empty(n, dtype=np.uint8)
    for i, (id_, citor_score, citee_score, coauthor, kind) \
            in enumerate(res_list):
        id_arr[i] = id_
        citor_score_arr[i] = citor_score
        citee_score_arr[i] = citee_score
        coauthor_arr[i] = coauthor
        kind_arr[i] = kind
    return id_arr, citor_score_arr, citee_score_arr, coauthor_arr, kind_arr


@nb.njit(nogil=True)
def _indices_to_ids(res, ind2id):
    for i in range(len(res)):
        index, citor_score, citee_score, coauthor, kind = res[i]
        id_ = ind2id[index]
        res[i] = id_, citor_score, citee_score, coauthor, kind


@nb.njit(nb.u4(id_mapping_arrs, nb.u4[::1]), nogil=True)
def _ids_to_ind(mapping, arr):
    """Replace all IDs in arr with indices in-place."""
    id2ind, ind2id, mask = mapping
    i = 0
    for id_ in arr:
        # Size is a power of 2, so (& mask) == (% len(id2ind)).
        hash_ = nb.u4(id_ * nb.u4(0x9e3779b1)) & mask
        while True:
            index = id2ind[hash_]
            if index == nb.u4(-1):
                break
            # id2ind[hash_] might be the correct index, but this is not
            # guaranteed due to collisions. Look it up in ind2id to make
            # sure.
            if ind2id[index] == id_:
                arr[i] = index
                i += 1
                break
            hash_ = nb.u4(hash_ + 1) & mask
    return i


@nb.njit(mmapped_arr(mapping_arrs, nb.u4), nogil=True)
def _traverse_one(mapping, i):
    """Given an index i, return the indices i maps tp.

    For example, if mapping maps papers to authors, then i must be a
    paper index, and this function returns an array of author indices.
    """
    ptr, ind = mapping
    start = ptr[i]
    end = ptr[i + 1]
    return ind[start:end]


@nb.njit(mapping_arrs(mapping_arrs, nb.u4), nogil=True)
def _traverse_citations(mapping, i):
    """Given a paper index i, return the citors and citees of i.

    This is similar to _traverse_one, but the citations mapping is a
    little different (it's two tables, not one).

    Returns a 2-tuple of arrays (citor indices, citee indices).
    """
    ptr, ind = mapping
    start_citors = ptr[2 * i]
    start_citees = ptr[2 * i + 1]
    end = ptr[2 * i + 2]
    return ind[start_citors:start_citees], ind[start_citees:end]


@nb.generated_jit(nopython=True, nogil=True)
def _is_in_range(range_, i):
    """Check if integer i is in range_.

    range_ is None or a 2-tuple of ints, but the type must be a
    compile-time constant. If range_ is None, returns True.
    """
    if isinstance(range_, nb.types.NoneType):
        return lambda range_, i: True
    else:
        return lambda range_, i: range_[0] <= i < range_[1]


@nb.njit(nogil=True)
def _is_self_citation(ego_entities, entity_ids):
    """Check if a paper is a self-citation.

    ego_entities are the authors/affiliations/etc. that are the centre
    of the flower, as a set. entity_ids is an iterable of the authors/-
    affiliations/etc. of the paper being checked.
    """
    for id_ in entity_ids:
        if id_ in ego_entities:
            return True
    return False


@nb.njit(nogil=True)
def _is_author(author_range, i):
    """Check if entity i is an author.

    author_range is an integer such that all indices in {0, ...,
    author_range - 1} represent authors.
    """
    return i < author_range


@nb.njit(nogil=True)
def _is_author_or_aff(aff_range, i):
    """Check if entity i is an affiliation.

    aff_range is an integer such that all indices in {0, ...,
    aff_range - 1} represent affiliations.
    """
    return i < aff_range


@nb.njit(nb.uint64(nb.uint64, nb.uint64[::1]), nogil=True)
def _get_year(paper_id, paper_year_map):
    for i, start in enumerate(paper_year_map):
        if paper_id < start:
            return i - 1
    raise RuntimeError()


dict_val = nb.types.Tuple([nb.u4, nb.f4])
result_val_t = nb.types.Tuple([nb.u4, nb.f4, nb.f4, nb.u1])


@nb.njit(nogil=True)
def _make_flower(
    entity_ids, paper_ids,
    entity2paper_map, paper2entity_map, citation_maps,
    *,
    pub_ids, cit_ids, self_citations, coauthors,
    author_range, aff_range,
):
    ego_entities = set(entity_ids)  # Entities forming the ego.
    ego_papers = set(paper_ids)  # All papers written by ego.
    coauthor_ids = set()  # All coauthors of ego.

    for entity_id in ego_entities:
        ego_papers.update(_traverse_one(entity2paper_map, entity_id))

    # Track influence on citor papers. Need weighted and unweighted
    # citation counts. Weighting affects authors and affiliations,
    # whereas unweighted scores are for venues and fields of study.
    citor_papers = nb.typed.Dict.empty(key_type=nb.u4, value_type=dict_val)
    # Track influence on citee papers. Only need unweighted citation
    # counts: weights are computed later.
    citee_papers = nb.typed.Dict.empty(key_type=nb.u4, value_type=nb.u4)
    for paper_id in ego_papers:
        paper_entities = _traverse_one(paper2entity_map, paper_id)
        coauthor_ids.update(paper_entities)

        if not _is_in_range(pub_ids, paper_id):
            continue

        num_authors = 0
        for entity_id in paper_entities:
            if not _is_author(author_range, entity_id):
                break  # Entity indices are sorted.
            num_authors += 1

        recip_weight = nb.f4(1) / nb.f4(max(num_authors, 1))
        citors, citees = _traverse_citations(citation_maps, paper_id)
        for citor_id in citors:
            # TODO: Again, this filtering can be more clever.
            if _is_in_range(cit_ids, citor_id):
                # Numba can't inline dictionary accesses, so this is two
                # function calls lol.
                count, score = citor_papers.get(citor_id,
                                                (nb.u4(0), nb.f4(0.)))
                citor_papers[citor_id] = count + 1, score + recip_weight
        for citee_id in citees:
            # TODO: Same optimization opportunity.
            if _is_in_range(pub_ids, citee_id):
                # Another two calls.
                citee_papers[citee_id] = nb.u4(
                    citee_papers.get(citee_id, nb.u4(0)) + nb.u4(1))

    # Map entity index to score (influencees).
    citor_entities = nb.typed.Dict.empty(key_type=nb.u4, value_type=nb.f4)
    for paper_id, (count, weight) in citor_papers.items():
        entity_ids = _traverse_one(paper2entity_map, paper_id)
        if not self_citations and _is_self_citation(ego_entities, entity_ids):
            continue
        for entity_id in entity_ids:
            # Yep, two more calls.
            citor_entities[entity_id] = (
                citor_entities.get(entity_id, nb.f4(0.))
                + (weight
                   if _is_author_or_aff(aff_range, entity_id)
                   else nb.f4(count)))

    # Map entity index to score (influencers).
    citee_entities = nb.typed.Dict.empty(key_type=nb.u4, value_type=nb.f4)
    for paper_id, count in citee_papers.items():
        entity_ids = _traverse_one(paper2entity_map, paper_id)
        if not self_citations and _is_self_citation(ego_entities, entity_ids):
            continue
        num_authors = 0
        for entity_id in entity_ids:
            if not _is_author(author_range, entity_id):
                break
            num_authors += 1
        # Difference from influencees: paper_id is the paper being
        # cited, so weight by (1 / num_authors).
        weight = nb.f4(count) / nb.f4(max(num_authors, 1))
        for entity_id in entity_ids:
            # Two non-inlined calls (:
            citee_entities[entity_id] = (
                citee_entities.get(entity_id, nb.f4(0.))
                + (weight
                   if _is_author_or_aff(aff_range, entity_id)
                   else nb.f4(count)))

    # Remove ego. Also remove coauthors if necessary.
    excluded_entities = ego_entities if coauthors else coauthor_ids
    for entity_id in excluded_entities:
        citor_entities.pop(entity_id, None)
        citee_entities.pop(entity_id, None)

    result = nb.typed.List.empty_list(result_val_t)
    for entity_id, citor_score in citor_entities.items():
        citee_score = citee_entities.pop(entity_id, nb.f4(0.))
        is_coauthor = nb.u1(entity_id in coauthor_ids)
        result.append((entity_id, citor_score, citee_score, is_coauthor))
    for entity_id, citee_score in citee_entities.items():
        is_coauthor = nb.u1(entity_id in coauthor_ids)
        result.append((entity_id, nb.f4(0.), citee_score, is_coauthor))
    return result


@nb.njit(nogil=True)
def _make_stats(
    entity_ids, paper_ids,
    entity2paper_map, citation_maps,
    *,
    paper_year_map,
):
    num_years, = paper_year_map.shape
    pub_year_counts = np.zeros(num_years, dtype=np.uint64)
    cit_year_counts = np.zeros((num_years, num_years), dtype=np.uint64)
    ref_count = 0
    ego_papers = set(paper_ids)
    for entity_id in entity_ids:
        ego_papers.update(_traverse_one(entity2paper_map, entity_id))
    for paper_id in ego_papers:
        pub_year = _get_year(paper_id, paper_year_map)
        pub_year_counts[pub_year] += 1
        citors, citees = _traverse_citations(citation_maps, paper_id)
        for citor_id in citors:
            cit_year = _get_year(citor_id, paper_year_map)
            cit_year_counts[pub_year, cit_year] += 1
        ref_count += len(citees)

    return pub_year_counts, cit_year_counts, ref_count


cite_map = nb.types.Tuple([nb.u4, nb.u4])


@nb.njit(nogil=True)
def _make_node_info(
    node_id,
    entity_ids, paper_ids,
    entity2paper_map, paper2entity_map, citation_maps,
    *,
    pub_ids, cit_ids, self_citations, coauthors,
    author_range, aff_range,
):
    ego_entities = set(entity_ids)  # Entities forming the ego.
    ego_papers = set(paper_ids)  # All papers written by ego.
    coauthor_ids = set()  # All coauthors of ego.

    for entity_id in ego_entities:
        ego_papers.update(_traverse_one(entity2paper_map, entity_id))

    # key_type = citor/citee_paper_id, value = paper_id
    citor_papers = nb.typed.List.empty_list(cite_map)
    citee_papers = nb.typed.List.empty_list(cite_map)
    for paper_id in ego_papers:
        paper_entities = _traverse_one(paper2entity_map, paper_id)
        coauthor_ids.update(paper_entities)

        if not _is_in_range(pub_ids, paper_id):
            continue

        citors, citees = _traverse_citations(citation_maps, paper_id)
        for citor_id in citors:
            entity_ids = _traverse_one(paper2entity_map, citor_id)
            if not self_citations and _is_self_citation(ego_entities, entity_ids):
                continue
            if node_id not in entity_ids:
                continue
            if _is_in_range(cit_ids, citor_id):
                citor_papers.append((citor_id, paper_id))

        for citee_id in citees:
            entity_ids = _traverse_one(paper2entity_map, citee_id)
            if not self_citations and _is_self_citation(ego_entities, entity_ids):
                continue
            if node_id not in entity_ids:
                continue
            if _is_in_range(pub_ids, citee_id):
                citee_papers.append((paper_id, citee_id))

    # print("citor_papers", citor_papers)
    # print("citee_papers", citee_papers)

    return citor_papers, citee_papers
