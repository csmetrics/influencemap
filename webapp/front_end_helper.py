import itertools
import operator
from functools import partial

import numpy as np
import pandas as pd

from core.search.elastic import (
    get_display_names_from_author_ids, get_display_names_from_conference_ids,
    get_display_names_from_fos_ids, get_display_names_from_journal_ids,
    get_names_from_affiliation_ids)




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
    subflowers, name_lookup_fs,
    *,
    gtype, flower_name,
):
    subflower_dfs = []
    for i, subflower in enumerate(subflowers):
        influencers_df = pd.DataFrame(
            subflower['influencers'].values(),
            index=map(int, subflower['influencers'].keys()),
            columns=['influenced'])
        influencees_df = pd.DataFrame(
            subflower['influencees'].values(),
            index=map(int, subflower['influencees'].keys()),
            columns=['influencing'])
        subflower_df = influencers_df.join(influencees_df, how='outer')
        subflower_df.fillna(0., inplace=True)
        subflower_df['type'] = i
        subflower_dfs.append(subflower_df)
    df = pd.concat(subflower_dfs)
    df['sum'] = df['influencing'] + df['influenced']
    df['dif'] = df['influencing'] - df['influenced']
    df['ratio'] = df['dif'] / df['sum']
    df['normed_sum'] = df['sum'] / df['sum'].max()
    df['normed_ratio'] = _make_normed_ratio(df['ratio'])
    df['normed_influenced'], df['normed_influencing'] = _normalize_double_log(
        df['influenced'], df['influencing'])

    # df.sort_values('sum', inplace=True, ascending=False)
    df['sort_tmp'] = np.maximum(df['influencing'], df['influenced'])
    df.sort_values('sort_tmp', inplace=True, ascending=False, kind='mergesort')
    del df['sort_tmp']    
    
    total = len(df)

    df = df.head(n=50)

    df['name'] = None
    for i, name_lookup_f in enumerate(name_lookup_fs):
        mask = df['type'] == i
        if mask.any():
            ids = tuple(df[mask].index)
            ids_to_name = name_lookup_f(ids)
            names = tuple(map(ids_to_name.get, ids, map(str, ids)))
            df.loc[mask, 'name'] = names

    df['bloom_order'] = range(1, len(df) + 1)

    nodes = [
        dict(name=flower_name, weight=1, id=0, gtype=gtype, size=1,
             bloom_order=0, coauthor=str(False))
    ]
    nodes.extend(
        dict(name=row.name, weight=row.normed_ratio, id=row[0], gtype=gtype,
             size=row.normed_sum, inf_in=row.influenced,
             inf_out=row.influencing, dif=row.dif, ratio=row.ratio,
             coauthor=str(False), bloom_order=row.bloom_order)
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
    pub_year_counts = {int(year): count
                       for year, count in pub_year_counts.items()
                       if count}
    cit_year_counts = {int(year): {int(year_): count
                                   for year_, count in year_counts.items()
                                   if count}
                       for year, year_counts in cit_year_counts.items()
                       if any(year_counts.values())}

    pub_range_start = min(pub_year_counts)
    pub_range_end = max(pub_year_counts)
    pub_range_len = pub_range_end - pub_range_start + 1
    cit_range_start = min(map(min, cit_year_counts.values()))
    cit_range_end = max(map(max, cit_year_counts.values()))
    cit_range_len = cit_range_end - cit_range_start + 1

    stats = dict(
        min_year=pub_range_start,
        max_year=pub_range_end,
        num_papers=pub_count,
        avg_papers=round(pub_count / pub_range_len, 1),
        num_refs=ref_count,
        avg_refs=round(ref_count / pub_count, 1),
        num_cites=cit_count,
        avg_cites=round(cit_count / pub_count, 1))

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


def make_response_data(
    flower,
    stats=None,
    *,
    is_curated=None,
    flower_name,
    session={},
    selection=None,
):
    res = {}

    if is_curated is not None:
        res['curated'] = is_curated
    res['navbarOption'] = NAVBAR_OPTIONS
    
    res['conf'] = _make_one_response_flower(
        [flower['journal_part'], flower['conference_series_part']],
        [get_display_names_from_journal_ids,
         get_display_names_from_conference_ids],
        gtype='conf', flower_name=flower_name)
    res['inst'] = _make_one_response_flower(
        [flower['affiliation_part']],
        [partial(get_names_from_affiliation_ids, with_id=True)],
        gtype='inst', flower_name=flower_name)
    res['fos'] = _make_one_response_flower(
        [flower['field_of_study_part']],
        [partial(get_display_names_from_fos_ids, with_id=True)],
        gtype='fos', flower_name=flower_name)
    res['author'] = _make_one_response_flower(
        [flower['author_part']],
        [partial(get_display_names_from_author_ids, with_id=True)],
        gtype='author', flower_name=flower_name)

    if stats is not None:
        res['stats'], res['yearSlider'] = make_year_slider_and_stats(
            stats['pub_year_counts'], stats['cit_year_counts'],
            stats['pub_count'], stats['cit_count'], stats['ref_count'],
            selection=selection)

    res['session'] = session

    return res
