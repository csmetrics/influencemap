#from webapp.graph                  import processdata
from core.flower.draw_flower_test  import draw_flower
from core.utils.get_entity         import entity_from_name
from core.search.query_info        import paper_info_check_query, paper_info_mag_check_multiquery
from core.score.agg_paper_info     import score_leaves
from core.score.agg_score          import agg_score_df, post_agg_score_df
from core.flower.node_info         import select_node_info
from core.score.agg_utils          import get_coauthor_mapping
from core.score.agg_utils          import flag_coauthor
from core.score.agg_filter         import filter_year
from core.flower.flower_bloom_data import score_df_to_graph
from core.utils.get_stats          import get_stats
from core.config                   import *

from datetime    import datetime
from collections import Counter
from operator    import itemgetter
from multiprocessing import Process, Queue

import numpy as np
import core.utils.entity_type as ent

flower_leaves = [ ('author', [ent.Entity_type.AUTH])
                , ('conf'  , [ent.Entity_type.CONF, ent.Entity_type.JOUR])
                , ('inst'  , [ent.Entity_type.AFFI])
                , ('fos'   , [ent.Entity_type.FSTD]) ]

str_to_ent = {
        'author': ent.Entity_type.AUTH,
        'conference': ent.Entity_type.CONF,
        'journal': ent.Entity_type.JOUR,
        'institution': ent.Entity_type.AFFI,
        'fieldofstudy': ent.Entity_type.FSTD,
    }

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
    t3 = datetime.now()

    data_list = []

    q = Queue()
    processes = []
    results = []
    for filter_type in range(4):
        p = Process(target=p_worker, args=(q, filter_type, agg_score, flower_type, flower_name, config))
        processes.append(p)
        p.start()
    for p in processes:
        ret = q.get()
        results.append(ret)
        p.join()
    data_list = sorted(results, key=itemgetter("filter_type"))

    t4 = datetime.now()

    print("[t]", t2-t1, "score_leaves")
    print("[t]", t3-t2, "agg_score_df")
    print("[t]", t4-t3, "processdata")

    return flower_type, data_list  #[data, data.copy(), data.copy()]#, data.copy()] #, node_info

def p_worker(queue, filter_type, agg_score, flower_type, flower_name, config):

    # Select the influence type from self citations
    if filter_type == 0:  #config['self_cite'] and config['icoauthor']:
        agg_score['influenced'] = agg_score.influenced_tot
        agg_score['influencing'] = agg_score.influencing_tot
    elif filter_type == 1:  #config['self_cite']:
        agg_score['influenced'] = agg_score.influenced_nca
        agg_score['influencing'] = agg_score.influencing_nca
    elif filter_type == 2:  #config['icoauthor']:
        agg_score['influenced'] = agg_score.influenced_nsc
        agg_score['influencing'] = agg_score.influencing_nsc
    else:  # filter_type == 3
        agg_score['influenced'] = agg_score.influenced_nscnca
        agg_score['influencing'] = agg_score.influencing_nscnca

    # Sort alphabetical first
    agg_score.sort_values('entity_name', ascending=False, inplace=True)

    # Sort by sum of influence
    agg_score['tmp_sort'] = agg_score.influencing + agg_score.influenced
    agg_score.sort_values('tmp_sort', ascending=False, inplace=True)

    # Sort by max of influence
    agg_score['tmp_sort'] = np.maximum(agg_score.influencing, agg_score.influenced)
    agg_score.sort_values('tmp_sort', ascending=False, inplace=True)
    agg_score.drop('tmp_sort', axis=1, inplace=True)

    # Need to take empty df into account
    if agg_score.empty:
        top_score = agg_score
        num_leaves = config['num_leaves']
    else:
        num_leaves = max(50, config['num_leaves'])
        top_score = agg_score.head(n=num_leaves)

    # Calculate post filter statistics (sum and ratio)
    top_score = post_agg_score_df(top_score)
    top_score.ego = flower_name

    # Calculate the bloom ordering
    top_score.loc[:,'bloom_order'] = range(1, len(top_score) + 1)

    # Graph score
    graph_score = score_df_to_graph(top_score)

    # D3 format
    data = processdata(flower_type, graph_score, num_leaves, config['order'], 0)
    #print('len(agg_score)', len(agg_score))

    data['filter_type'] = filter_type
    data['total'] = len(agg_score)

    queue.put(data)
