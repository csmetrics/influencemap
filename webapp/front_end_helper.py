import itertools
from functools import partial

import numpy as np
import pandas as pd

from core.search.elastic import (
    get_display_names_from_author_ids, get_display_names_from_journal_ids,
    get_display_names_from_conference_ids, get_names_from_affiliation_ids)




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


def _make_one_response_flower(subflowers, name_lookup_fs, *, gtype):
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
            names = tuple(map(ids_to_name.__getitem__, map(int, ids)))
            df.loc[mask, 'name'] = names

    df['bloom_order'] = range(1, 51)

    nodes = [
        dict(name='ego', weight=1, id=0, gtype=gtype, size=1, bloom_order=0,
             coauthor=str(False))
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
    return [dict(nodes=nodes, links=links, bars=bars, total=total)] * 3


def make_response_data(
    flower,
    *,
    is_curated,
):
    res = {}

    res['curated'] = is_curated
    res['stats'] = {'min_year': 1950, 'max_year': 2012, 'num_papers': 70, 'avg_papers': 1.1, 'num_refs': 147, 'avg_refs': 2, 'num_cites': 1199, 'avg_cites': 17}
    res['navbarOption'] = {'optionlist': [{'id': 'author', 'name': 'Author'}, {'id': 'conference', 'name': 'Conference'}, {'id': 'journal', 'name': 'Journal'}, {'id': 'institution', 'name': 'Institution'}, {'id': 'paper', 'name': 'Paper'}], 'selectedKeyword': '', 'selectedOption': {'id': 'author', 'name': 'Author'}}
    res['yearSlider'] = {'title': 'Publications range', 'pubrange': [1950, 2012, 63], 'citerange': [1950, 2018, 69], 'pubChart': [], 'citeChart': [], 'selected': {'pub_lower': 1950, 'pub_upper': 2012, 'cit_lower': 1950, 'cit_upper': 2018, 'self_cite': 'false', 'icoauthor': 'true', 'cmp_ref': 'false', 'num_leaves': 25, 'order': 'ratio'}}
    
    
    res['conf'] = _make_one_response_flower(
        [flower['journal_part'], flower['conference_series_part']],
        [get_display_names_from_journal_ids,
         get_display_names_from_conference_ids],
        gtype='conf')
    res['inst'] = _make_one_response_flower(
        [flower['affiliation_part']],
        [partial(get_names_from_affiliation_ids, with_id=True)],
        gtype='inst')
    res['fos'] = _make_one_response_flower(
        [flower['field_of_study_part']],
        [lambda ids: {id_: str(id_) for id_ in ids}],
        gtype='fos')
    res['author'] = _make_one_response_flower(
        [flower['author_part']],
        [partial(get_display_names_from_author_ids, with_id=True)],
        gtype='author')

    return res
