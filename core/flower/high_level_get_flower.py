from core.score.agg_paper_info     import score_leaves
from core.score.agg_score          import agg_score_df, post_agg_score_df
from core.score.agg_filter         import filter_year
from core.flower.flower_bloom_data import score_df_to_graph
from core.config                   import *

from datetime    import datetime
from operator    import itemgetter

import numpy as np

def default_config():
        return {
        'self_cite': False,
        'icoauthor': True,
        'pub_lower': None,
        'pub_upper': None,
        'cit_lower': None,
        'cit_upper': None,
        'num_leaves': 25,
        'order': 'ratio',
        }

def processdata(gtype, egoG, num_leaves, order, filter_num):
    center_node = egoG.graph['ego']

    # Radius of circle
    radius = 1.2

    # Get basic node information from ego graph
    outer_nodes = list(egoG)
    outer_nodes.remove('ego')

    outer_nodes.sort(key=lambda n: min(-egoG.nodes[n]['inf_out'], -egoG.nodes[n]['inf_in']))

    links = list(egoG.edges(data=True))

    # Sort by name, influence dif, then ratio

    links.sort(key=lambda l: (l[0], l[1]))
    links.sort(key=lambda l: -l[2]['sumw'])

    links_in  = [l for l in links if l[2]['direction'] == 'in']
    links_out = [l for l in links if l[2]['direction'] == 'out']

    # Make sure in/out bars are in order
    links = list()
    for l_in, l_out in zip(links_in, links_out):
        links.append(l_out)
        links.append(l_in)

    if num_leaves > 25:
        anglelist = np.linspace(np.pi*(1+(num_leaves-25)/num_leaves/2), -np.pi*(num_leaves-25)/num_leaves/2, num=len(outer_nodes))
    elif num_leaves < 10:
        anglelist = np.linspace((0.5+num_leaves/20)*np.pi, (0.5-num_leaves/20)*np.pi, num=len(outer_nodes))
    else:
        anglelist = np.linspace(np.pi, 0., num=len(outer_nodes))
    x_pos = [0]; x_pos.extend(list(radius * np.cos(anglelist)))
    y_pos = [0]; y_pos.extend(list(radius * np.sin(anglelist)))

    # Outer nodes data
    nodedata = { key:{
            'name': key,
            'weight': egoG.nodes[key]['nratiow'],
            'id': i,
            'gtype': gtype,
            'size': egoG.nodes[key]['sumw'],
            'sum': egoG.nodes[key]['sum'],
            'xpos': x_pos[i],
            'ypos': y_pos[i],
            'inf_in': egoG.nodes[key]['inf_in'],
            'inf_out': egoG.nodes[key]['inf_out'],
            'dif': egoG.nodes[key]['dif'],
            'ratio': egoG.nodes[key]['ratiow'],
            'coauthor': str(egoG.nodes[key]['coauthor']),
            'bloom_order': egoG.nodes[key]['bloom_order'],
            'filter_num': filter_num,
        } for i, key in zip(range(1, len(outer_nodes)+1), outer_nodes)}

    nodekeys = ['ego'] + [v['name'] for v in sorted(nodedata.values(), key=itemgetter('id'))]

    # Center node data
    nodedata['ego'] = {
        'name': egoG.nodes['ego']['name'],
        'weight': 1,
        'id': 0,
        'gtype': gtype,
        'size': 1,
        'xpos': x_pos[0],
        'ypos': y_pos[0],
        'bloom_order': 0,
        'coauthor': str(False),
        'filter_num': filter_num,
    }

    edge_in = [{
            'source': nodekeys.index(s),
            'target': nodekeys.index(t),
            'padding': nodedata[t]['size'],
            'id': nodedata[t]['id'],
            'gtype': gtype,
            'type': v['direction'],
            'weight': v['nweight'],
            'o_weight': v['weight'],
            'bloom_order': nodedata[t]['bloom_order'],
            'filter_num': filter_num,
        } for s, t, v in links_in]

    edge_out = [{
            'source': nodekeys.index(s),
            'target': nodekeys.index(t),
            'padding': nodedata[t]['size'],
            'id': nodedata[s]['id'],
            'gtype': gtype,
            'type': v['direction'],
            'weight': v['nweight'],
            'o_weight': v['weight'],
            'bloom_order': nodedata[s]['bloom_order'],
            'filter_num': filter_num,
        } for s, t, v in links_out]

    linkdata = list()

    for lin, lout in zip(edge_in, edge_out):
        linkdata.append(lin)
        linkdata.append(lout)

    chartdata = [{
            'id': nodedata[t]['id'] if v['direction'] == 'in' else nodedata[s]['id'],
            'bloom_order': nodedata[t]['bloom_order'] if v['direction'] == 'in' else nodedata[s]['bloom_order'],
            'name': t if v['direction'] == 'in' else s,
            'type': v['direction'],
            'gtype': gtype,
            'sum': nodedata[t]['weight'] if v['direction'] == 'in' else nodedata[s]['weight'],
            'weight': v['weight'],
            'filter_num': filter_num,
        } for s, t, v in links]

    chartdata.sort(key=lambda d: d['bloom_order'])

    return { 'nodes': sorted(list(nodedata.values()), key=itemgetter('id')), 'links': linkdata, 'bars': chartdata }


def gen_flower_data(score_df, flower_prop, entity_names, flower_name,
                    config=default_config):
    '''
    '''
    # Flower properties
    flower_type, leaves = flower_prop
    print('[gen_flower_data] flower_type', flower_type)

    t1 = datetime.now()
    print(datetime.now(), 'start score_leaves')
    entity_score = score_leaves(score_df, leaves)
    print(datetime.now(), 'finish score_leaves')

    # Ego name removal
    if (flower_type != 'conf'):
        entity_score = entity_score[~entity_score['entity_name'].str.lower()\
                .isin(entity_names)]

    # Filter publication year for ego's paper
    filter_score = filter_year(entity_score, config['pub_lower'],
                                             config['pub_upper'])

    # Filter Citation year for reference links
    filter_score = filter_year(filter_score, config['cit_lower'],
                                             config['cit_upper'],
                                             index = 'influence_year')
    t2 = datetime.now()

    # Aggregate
    agg_score = agg_score_df(filter_score)
    # print(agg_score)

    # Select the influence type from self citations
    if config['self_cite'] and config['icoauthor']:
        agg_score['influenced'] = agg_score.influenced_tot
        agg_score['influencing'] = agg_score.influencing_tot
    elif config['self_cite']:
        agg_score['influenced'] = agg_score.influenced_nca
        agg_score['influencing'] = agg_score.influencing_nca
    elif config['icoauthor']:
        agg_score['influenced'] = agg_score.influenced_nsc
        agg_score['influencing'] = agg_score.influencing_nsc
    else:
        agg_score['influenced'] = agg_score.influenced_nscnca
        agg_score['influencing'] = agg_score.influencing_nscnca

    # Sort by sum of influence
    agg_score['tmp_sort'] = agg_score.influencing + agg_score.influenced
    agg_score.sort_values('tmp_sort', ascending=False, inplace=True)

    # Sort by max of influence
    agg_score['tmp_sort'] = np.maximum(agg_score.influencing, agg_score.influenced)
    agg_score.sort_values('tmp_sort', ascending=False, inplace=True)
    agg_score.drop('tmp_sort', axis=1, inplace=True)

    top_score = agg_score[['entity_name', 'coauthor', 'influenced', 'influencing']].head(25)

    data = []
    for values in top_score.to_dict('records'):
        name = values['entity_name']
        score_df = filter_score[filter_score['entity_name'] == name]
        score_df = score_df.groupby(['influence_year', 'publication_year']).agg({'influenced':'sum', 'influencing':'sum'}).reset_index()
        values['year'] = score_df.to_dict('records')
        data.append(values)

    return data
