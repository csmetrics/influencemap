import json
import mmap
import pathlib

import numba as nb
import numpy as np

mmapped_arr = nb.types.Array(nb.u4, 1, 'C', readonly=True)
mapping_arrs = nb.types.Tuple([mmapped_arr, mmapped_arr])
id_mapping_arrs = nb.types.Tuple([mmapped_arr, mmapped_arr, nb.u4])


class ResArrs:
    """Holder for ID and score arrays."""
    __slots__ = ['ids', 'scores', 'coauthors']
    def __init__(self, ids, scores, coauthors):
        self.ids = ids
        self.scores = scores
        self.coauthors = coauthors


class PartFlower:
    """Result for a particular entity type."""
    __slots__ = ['influencers', 'influencees']
    def __init__(self, res=None, *, influencers=None, influencees=None):
        if ((res is None, influencers is None, influencees is None)
                not in ((True, False, False), (False, True, True))):
            raise ValueError('either res or influencers and '
                             'must be provided')
        if res is not None:
            influencers, influencees = res
        self.influencers = influencers
        self.influencees = influencees


class Flower:
    """Full result."""
    __slots__ = ['author_part', 'affiliation_part', 'field_of_study_part',
                 'journal_part', 'conference_series_part']
    def __init__(
        self,
        *,
        author_part, affiliation_part, field_of_study_part,
        journal_part, conference_series_part,
    ):
        self.author_part = author_part
        self.affiliation_part = affiliation_part
        self.field_of_study_part = field_of_study_part
        self.journal_part = journal_part
        self.conference_series_part = conference_series_part


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
        self.ptr = np.frombuffer(self.ptr_mmap, dtype=np.uint32)
        with open(ind_path, 'rb') as f:
            self.ind_mmap = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        self.ind = np.frombuffer(self.ind_mmap, dtype=np.uint32)

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
        self.ind2id = np.frombuffer(self.ind2id_mmap, dtype=np.uint32)

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
        self.id2ind = np.frombuffer(self.id2ind_mmap, dtype=np.uint32)
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
        self.paper_year_map = np.array(paper_year_map, dtype=np.uint32)
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
        uint32s.
        """
        if years is None:
            return None
        start_year, end_year = years
        start_id = self.year_starts[start_year]
        end_id = self.year_starts[end_year]
        return nb.u4(start_id), nb.u4(end_id)

    def _ids_to_indices(self, ids, mapper, allow_not_found):
        """Convert IDs to indices."""
        indices = np.array(ids, dtype=np.uint32)
        length = _ids_to_ind(mapper.arrs, indices)
        if not allow_not_found and lenth < len(indices):
            raise KeyError('id not found')
        return indices[:length]

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

    def _make_flower_from_res(
        self,
        influencers, influencees,
    ):
        """Turn result dicts returned by _make_flower into a Flower."""
        split_influencers = split_res(
            influencers, self.author_range, self.aff_range, self.fos_range,
            self.journal_range, self.cs_range, self.fos_l1_start)
        split_influencees = split_res(
            influencees, self.author_range, self.aff_range, self.fos_range,
            self.journal_range, self.cs_range, self.fos_l1_start)

        ind2id = self.entity_ind2id_map.arrs
        for res_arrs in split_influencers:
            _indices_to_ids(res_arrs, ind2id)
        for res_arrs in split_influencees:
            _indices_to_ids(res_arrs, ind2id)

        author_res, aff_res, fos_res, journal_res, cs_res = zip(
            split_influencers, split_influencees)

        author_part = PartFlower(starmap(ResArrs, author_res))
        aff_part = PartFlower(starmap(ResArrs, aff_res))
        fos_part = PartFlower(starmap(ResArrs, fos_res))
        journal_part = PartFlower(starmap(ResArrs, journal_res))
        cs_part = PartFlower(starmap(ResArrs, cs_res))

        return Flower(author_part=author_part,
                      affiliation_part=aff_part,
                      field_of_study_part=fos_part,
                      journal_part=journal_part,
                      conference_series_part=cs_part)

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
        influencers, influencees = _make_flower(
            entity_indices, paper_indices,
            self.entity2paper_map.arrs,
            self.paper2entity_map.arrs,
            self.citation_maps.arrs,
            pub_ids=pub_ids, cit_ids=cit_ids,
            self_citations=nb.literally(bool(self_citations)),
            coauthors=nb.literally(bool(coauthors)),
            author_range=nb.literally(self.author_range),
            aff_range=nb.literally(self.aff_range))
        return self._make_flower_from_res(influencers, influencees)

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

        # nb.literally makes it a compile-time constant. This does
        # require one compilation per value.
        pub_year_counts, cit_year_counts, ref_count = _make_stats(
            entity_indices, paper_indices,
            self.entity2paper_map.arrs,
            self.citation_maps.arrs,
            paper_year_map=self.paper_year_map)
        return self._make_stats_from_arrs(
            pub_year_counts, cit_year_counts, ref_count)


@nb.njit(nogil=True)
def empty_res_lists():
    return (nb.typed.List.empty_list(nb.u4),
            nb.typed.List.empty_list(nb.f4),
            nb.typed.List.empty_list(nb.u1))


@nb.njit(nogil=True)
def res_lists_append(res_lists, id_, score, coauthor):
    id_list, score_list, coauthor_list = res_lists
    id_list.append(id_)
    score_list.append(score)
    coauthor_list.append(coauthor)


@nb.njit(nogil=True)
def res_lists_to_arrs(res_lists):
    id_list, score_list, coauthor_list = res_lists
    return (np.array(id_list, dtype=np.uint32),
            np.array(score_list, dtype=np.float32),
            np.array(coauthor_list, dtype=np.uint8))


@nb.njit(nogil=True)
def split_res(
    res,
    author_range, aff_range, fos_range, journal_range, cs_range,
    fos_l1_start,
):
    """Split a dict of indices and scores by entity type."""
    author_res = empty_res_lists()
    aff_res = empty_res_lists()
    fos_res = empty_res_lists()
    journals_res = empty_res_lists()
    cs_res = empty_res_lists()
    for index, score, coauthor in zip(*res):
        if index < author_range:
            res_lists_append(author_res, index, score, coauthor)
        elif index < aff_range:
            res_lists_append(aff_res, index, score, coauthor)
        elif index < fos_l1_start:
            pass  # Skip l0 fields of study.
        elif index < fos_range:
            res_lists_append(fos_res, index, score, coauthor)
        elif index < journal_range:
            res_lists_append(journals_res, index, score, coauthor)
        elif index < cs_range:
            res_lists_append(cs_res, index, score, coauthor)
        else:
            raise IndexError('entity index out of range')
    return (res_lists_to_arrs(author_res), res_lists_to_arrs(aff_res),
            res_lists_to_arrs(fos_res), res_lists_to_arrs(journals_res),
            res_lists_to_arrs(cs_res))


@nb.njit(nogil=True)
def _indices_to_ids(res, ind2id):
    res_ids, _, _ = res
    for i, index in enumerate(res_ids):
        res_ids[i] = ind2id[index]


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


@nb.njit(nb.uint32(nb.uint32, nb.uint32[::1]), nogil=True)
def _get_year(paper_id, paper_year_map):
    for i, start in enumerate(paper_year_map):
        if paper_id < start:
            return i - 1
    raise RuntimeError()


dict_val = nb.types.Tuple([nb.u4, nb.f4])

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

    citor_ids = np.empty(len(citor_entities), dtype=np.uint32)
    citor_scores = np.empty(len(citor_entities), dtype=np.float32)
    for i, (id_, score) in enumerate(citor_entities.items()):
        citor_ids[i] = id_
        citor_scores[i] = score

    citee_ids = np.empty(len(citee_entities), dtype=np.uint32)
    citee_scores = np.empty(len(citee_entities), dtype=np.float32)
    for i, (id_, score) in enumerate(citee_entities.items()):
        citee_ids[i] = id_
        citee_scores[i] = score

    # Could make these bitfields.
    citor_coauthors = np.zeros(len(citor_entities), dtype=np.uint8)
    citee_coauthors = np.zeros(len(citee_entities), dtype=np.uint8)
    if coauthors:
        for i, id_ in citor_ids:
            citor_coauthors[i] = id_ in coauthor_ids
        for i, id_ in citee_ids:
            citee_coauthors[i] = id_ in coauthor_ids

    return ((citor_ids, citor_scores, citor_coauthors),
            (citee_ids, citee_scores, citee_coauthors))


@nb.njit(nogil=True)
def _make_stats(
    entity_ids, paper_ids,
    entity2paper_map, citation_maps,
    *,
    paper_year_map,
):
    num_years, = paper_year_map.shape
    pub_year_counts = np.zeros(num_years, dtype=np.uint32)
    cit_year_counts = np.zeros((num_years, num_years), dtype=np.uint32)
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
