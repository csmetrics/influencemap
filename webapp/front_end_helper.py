import itertools
import logging
import os
import resource
import sys
import time
from functools import partial

import numpy as np
import pandas as pd

from concurrent.futures import ThreadPoolExecutor, as_completed

from core.search.local import (
    get_display_names_from_author_ids, get_display_names_from_conference_ids,
    get_display_names_from_fos_ids, get_display_names_from_journal_ids,
    get_names_from_affiliation_ids)


_helper_log = logging.getLogger('helper_memlog')
_helper_log.setLevel(logging.INFO)
if not _helper_log.handlers:
    _h = logging.StreamHandler(sys.stderr)
    _h.setFormatter(logging.Formatter('[%(asctime)s] [HELPER] %(message)s'))
    _helper_log.addHandler(_h)


def _stamp(msg):
    try:
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024)
    except Exception:
        rss = -1.0
    _helper_log.info('%s rss=%.2fGB pid=%d', msg, rss, os.getpid())


def _make_normed_ratio(series):
    c = max(abs(series.min()), abs(series.max()))
    if c == 0:
        return .5
    return (series + c) / (2 * c)


def _normalize_double_log(series1, series2):
    max_val = max(series1.max(), series2.max())
    if max_val == 0:
        return series1, series2
    return np.log2(1 + series1 / max_val), np.log2(1 + series2 / max_val)


def _make_one_response_flower(
    subflower, name_lookup_fs,
    *,
    gtype, flower_name,
):
    _stamp(f'{gtype} enter n_ids={len(subflower.get("ids", []))} '
           f'total={subflower.get("total")}')
    df_original = pd.DataFrame(dict(
        ids=subflower['ids'],
        influencing=subflower['citee_scores'],
        influenced=subflower['citor_scores'],
        coauthors=subflower['coauthors'],
        type=subflower['kinds']))
    _stamp(f'{gtype} df built rows={len(df_original)}')

    df_original['name'] = None
    for i, name_lookup_f in name_lookup_fs.items():
        mask = df_original['type'] == i
        n = int(mask.sum())
        if mask.any():
            ids = tuple(df_original[mask]['ids'])
            _stamp(f'{gtype} lookup type={i} n_ids={n} calling name_lookup_f')
            ids_to_name = name_lookup_f(ids)
            _stamp(f'{gtype} lookup type={i} done '
                   f'n_returned={len(ids_to_name)}')
            names = tuple(
                [ids_to_name[id] if id in ids_to_name else 'none' for id in ids])
            df_original.loc[mask, 'name'] = names

    # Name deduplication
    # IDs with the same names are grouped and stored in allids (array)
    # min(IDs) is used as the unique ID
    df = df_original.groupby('name', as_index=False).agg(
        influencing=('influencing', 'sum'),
        influenced=('influenced', 'sum'),
        type=('type', 'min'),
        coauthors=('coauthors', 'any'),
        ids=('ids', 'min'),
        allids=('ids', lambda tdf: tdf.unique().tolist()))
    df.set_index('ids', inplace=True)

    df['sum'] = df['influencing'] + df['influenced']
    df['dif'] = df['influencing'] - df['influenced']
    df['ratio'] = df['dif'] / df['sum']
    df['normed_sum'] = df['sum'] / df['sum'].max()
    df['normed_ratio'] = _make_normed_ratio(df['ratio'])
    df['normed_influenced'], df['normed_influencing'] = _normalize_double_log(
        df['influenced'], df['influencing'])
    total = subflower['total']

    df = df.sort_values(by=['sum'], ascending=False)
    df['bloom_order'] = range(1, len(df) + 1)

    nodes = [
        dict(name=flower_name, weight=1, id=0, gtype=gtype, size=1,
             bloom_order=0, coauthor=str(False))
    ]
    nodes.extend(
        dict(name=row.name, weight=row.normed_ratio, id=row[0], ids=row.allids,
             gtype=gtype, size=row.normed_sum, inf_in=row.influenced,
             inf_out=row.influencing, dif=row.dif, ratio=row.ratio,
             coauthor=str(row.coauthors), bloom_order=row.bloom_order)
        for row in df.itertuples()
    )

    links = [
        dict(source=0, target=i + 1, padding=row.normed_sum, id=row[0],
             gtype=gtype, type='in', weight=row.normed_influenced,
             bloom_order=row.bloom_order)
        for i, row in enumerate(df.itertuples())
    ]
    links.extend(
        dict(source=i + 1, target=0, padding=row.normed_sum, id=row[0],
             gtype=gtype, type='out', weight=row.normed_influencing,
             bloom_order=row.bloom_order)
        for i, row in enumerate(df.itertuples())
    )

    bars_in = (
        dict(
            id=row[0],
            bloom_order=row.bloom_order,
            name=row.name,
            type='in',
            gtype=gtype,
            weight=row.influenced,
        )
        for i, row in enumerate(df.itertuples())
    )
    bars_out = (
        dict(
            id=row[0],
            bloom_order=row.bloom_order,
            name=row.name,
            type='out',
            gtype=gtype,
            weight=row.influencing,
        )
        for i, row in enumerate(df.itertuples())
    )
    bars = list(itertools.chain.from_iterable(zip(bars_in, bars_out)))
    _stamp(f'{gtype} return n_nodes={len(nodes)} n_links={len(links)}')
    return [dict(nodes=nodes, links=links, bars=bars, total=total)]


NAVBAR_OPTIONS = {
    'optionlist': [{'id': 'author', 'name': 'Author'},
                   {'id': 'conference', 'name': 'Conference'},
                   {'id': 'journal', 'name': 'Journal'},
                   {'id': 'institution', 'name': 'Institution'},
                   {'id': 'paper', 'name': 'Paper'}],
    'selectedKeyword': '',
    'selectedOption': {'id': 'author', 'name': 'Author'}}


def make_year_slider_and_stats(
    pub_year_counts, cit_year_counts, pub_count, cit_count, ref_count,
    *,
    selection=None,
):
    # Sentinel guard: konigsberg's paper-years.json ranges through the
    # uint16 sentinel (65535) for "missing year" markers. A single
    # sentinel key made cit_chart below iterate range(min_year, 65536) —
    # tens of thousands of iterations each allocating an inner list of
    # the same length. Filter unreasonable years before any range()
    # computation.
    _MAX_YEAR = 2200
    pub_year_counts = {int(year): count
                       for year, count in pub_year_counts.items()
                       if count and int(year) <= _MAX_YEAR}
    _filtered_cit = {}
    for year, year_counts in cit_year_counts.items():
        if int(year) > _MAX_YEAR:
            continue
        inner = {int(y_): c for y_, c in year_counts.items()
                 if c and int(y_) <= _MAX_YEAR}
        if inner:
            _filtered_cit[int(year)] = inner
    cit_year_counts = _filtered_cit

    pub_range_start = min(pub_year_counts) if pub_year_counts else 0
    pub_range_end = max(pub_year_counts) if pub_year_counts else 0
    pub_range_len = pub_range_end - pub_range_start + 1
    cit_range_start = min(map(min, cit_year_counts.values())
                          ) if cit_year_counts else 0
    cit_range_end = max(map(max, cit_year_counts.values())
                        ) if cit_year_counts else 0
    cit_range_len = cit_range_end - cit_range_start + 1

    stats = dict(
        min_year=pub_range_start,
        max_year=pub_range_end,
        num_papers=pub_count,
        avg_papers=round(pub_count / pub_range_len,
                         1) if pub_range_len > 0 else 0,
        num_refs=ref_count,
        avg_refs=round(ref_count / pub_count, 1) if pub_count > 0 else 0,
        num_cites=cit_count,
        avg_cites=round(cit_count / pub_count, 1) if pub_count > 0 else 0)

    chart_start = min(pub_range_start, cit_range_start)
    chart_end = max(pub_range_end, cit_range_end)

    pub_chart = [
        dict(year=year, value=pub_year_counts.get(year, 0))
        for year in range(chart_start, chart_end + 1)
    ]
    cit_chart = [
        dict(year=year,
             value=[
                 dict(year=year_,
                      value=cit_year_counts.get(year, {}).get(year_, 0))
                 for year_ in range(chart_start, chart_end + 1)
             ])
        for year in range(chart_start, chart_end + 1)
    ]

    year_slider = dict(
        title='Publications range',
        pubrange=[pub_range_start, pub_range_end, pub_range_len],
        citerange=[cit_range_start, cit_range_end, cit_range_len],
        pubChart=pub_chart,
        citeChart=cit_chart,
        selected=dict(
            pub_lower=pub_range_start,
            pub_upper=pub_range_end,
            cit_lower=cit_range_start,
            cit_upper=cit_range_end,
            self_cite='false',
            icoauthor='true',
            cmp_ref='false',
            num_leaves=25,
            order='ratio',
        )
    )

    if selection is not None:
        selected = year_slider['selected']
        pub_years = selection.get('pub_years')
        if pub_years is not None:
            selected['pub_lower'], selected['pub_upper'] = pub_years
        cit_years = selection.get('cit_years')
        if cit_years is not None:
            selected['cit_lower'], selected['cit_upper'] = cit_years
        selected['self_cite'] = str(selection.get(
            'self_citations', selected['self_cite'])).lower()
        selected['icoauthor'] = str(selection.get(
            'coauthors', selected['icoauthor'])).lower()

    return stats, year_slider


def execute_parallel(args):
    gtype, flower_data, func_dict, flower_name = args
    _stamp(f'execute_parallel enter gtype={gtype}')
    try:
        result = _make_one_response_flower(
            flower_data, func_dict, gtype=gtype, flower_name=flower_name)
    except Exception as e:
        _stamp(f'execute_parallel EXCEPTION gtype={gtype}: {e!r}')
        raise
    _stamp(f'execute_parallel exit gtype={gtype}')
    return gtype, result


def make_response_data(
    flower,
    stats=None,
    *,
    is_curated=None,
    flower_name,
    session={},
    selection=None,
):

    functions = [
        ('conf', flower['venue'], {
         4: get_display_names_from_journal_ids, 2: get_display_names_from_conference_ids}, flower_name),
        ('inst', flower['affiliation'], {
         1: partial(get_names_from_affiliation_ids, with_id=True)}, flower_name),
        ('fos', flower['field_of_study'], {
         3: partial(get_display_names_from_fos_ids, with_id=True)}, flower_name),
        ('author', flower['author'], {
         0: partial(get_display_names_from_author_ids, with_id=True)}, flower_name)
    ]

    res = {}

    if is_curated is not None:
        res['curated'] = is_curated
    res['navbarOption'] = NAVBAR_OPTIONS

    # Execute in parallel
    _stamp(f'make_response_data: submitting {len(functions)} parallel tasks')
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(
            execute_parallel, func): func for func in functions}
        for future in as_completed(futures):
            gtype, result = future.result()
            _stamp(f'make_response_data: got result for {gtype}')
            res[gtype] = result
    _stamp('make_response_data: all parallel tasks done')

    if stats is not None:
        _stamp('make_response_data: calling make_year_slider_and_stats')
        res['stats'], res['yearSlider'] = make_year_slider_and_stats(
            stats['pub_year_counts'], stats['cit_year_counts'],
            stats['pub_count'], stats['cit_count'], stats['ref_count'],
            selection=selection)
        _stamp('make_response_data: make_year_slider_and_stats done')

    res['session'] = session

    _stamp('make_response_data: RETURN')
    return res
