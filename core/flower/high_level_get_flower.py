#from webapp.graph                  import processdata
from core.flower.draw_flower_test  import draw_flower
from core.utils.get_entity         import entity_from_name
from core.search.query_paper       import paper_query
from core.search.query_paper_mag   import paper_mag_multiquery
from core.search.query_info        import paper_info_check_query, paper_info_mag_check_multiquery
from core.score.agg_paper_info     import score_leaves
from core.score.agg_score          import agg_score_df#, select_node_info
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

import numpy as np
import core.utils.entity_type as ent

flower_leaves = [ ('author', [ent.Entity_type.AUTH])
                , ('conf'  , [ent.Entity_type.CONF, ent.Entity_type.JOUR])
                , ('inst'  , [ent.Entity_type.AFFI])
                , ('fos'   , [ent.Entity_type.FSTD]) ]

str_to_ent = {
        "author": ent.Entity_type.AUTH,
        "conference": ent.Entity_type.CONF,
        "journal": ent.Entity_type.JOUR,
        "institution": ent.Entity_type.AFFI,
        "fieldofstudy": ent.Entity_type.FSTD,
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

def processdata(gtype, egoG, num_leaves, order):
    center_node = egoG.graph['ego']

    # Radius of circle
    radius = 1.2

    # Get basic node information from ego graph
    outer_nodes = list(egoG)
    outer_nodes.remove('ego')

    # Sort by name, influence dif, then ratio
    outer_nodes.sort()
    if order == 'blue':
        outer_nodes.sort(key=lambda n: -egoG.nodes[n]['inf_out'])
    elif order == 'red':
        outer_nodes.sort(key=lambda n: -egoG.nodes[n]['inf_in'])
    elif order == 'total':
        outer_nodes.sort(key=lambda n: -egoG.nodes[n]['dif'])
        outer_nodes.sort(key=lambda n: -egoG.nodes[n]['sumw'])
    else:
        outer_nodes.sort(key=lambda n: -egoG.nodes[n]['dif'])
        outer_nodes.sort(key=lambda n: -egoG.nodes[n]['ratiow'])

    links = list(egoG.edges(data=True))

    # Sort by name, influence dif, then ratio
    links.sort(key=lambda l: (l[0], l[1]))
    if order == 'blue':
        links.sort(key=lambda l: -l[2]['inf_out'])
    elif order == 'red':
        links.sort(key=lambda l: -l[2]['inf_in'])
    elif order == 'total':
        links.sort(key=lambda l: -l[2]['dif'])
        links.sort(key=lambda l: -l[2]['sumw'])
    else:
        links.sort(key=lambda l: -l[2]['dif'])
        links.sort(key=lambda l: -l[2]['ratiow'])
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
    print(anglelist)
    print(np.linspace(np.pi, 0., num=len(outer_nodes)))
    x_pos = [0]; x_pos.extend(list(radius * np.cos(anglelist)))
    y_pos = [0]; y_pos.extend(list(radius * np.sin(anglelist)))

    # Outer nodes data
    nodedata = { key:{
            "name": key,
            "weight": egoG.nodes[key]["nratiow"],
            "id": i,
            "gtype": gtype,
            "size": egoG.nodes[key]["sumw"],
            "xpos": x_pos[i],
            "ypos": y_pos[i],
            "coauthor": str(egoG.nodes[key]['coauthor'])
        } for i, key in zip(range(1, len(outer_nodes)+1), outer_nodes)}

    nodekeys = ['ego'] + [v["name"] for v in sorted(nodedata.values(), key=itemgetter("id"))]

    # Center node data
    nodedata['ego'] = {
        "name": egoG.nodes['ego']['name'],
        "weight": 1,
        "id": 0,
        "gtype": gtype,
        "size": 1,
        "xpos": x_pos[0],
        "ypos": y_pos[0],
        "coauthor": str(False)
    }

    edge_in = [{
            "source": nodekeys.index(s),
            "target": nodekeys.index(t),
            "padding": nodedata[t]["size"],
            "id": nodedata[t]["id"],
            "gtype": gtype,
            "type": v["direction"],
            "weight": v["nweight"]
        } for s, t, v in links_in]

    edge_out = [{
            "source": nodekeys.index(s),
            "target": nodekeys.index(t),
            "padding": nodedata[t]["size"],
            "id": nodedata[s]["id"],
            "gtype": gtype,
            "type": v["direction"],
            "weight": v["nweight"]
        } for s, t, v in links_out]

    linkdata = list()

    for lin, lout in zip(edge_in, edge_out):
        linkdata.append(lin)
        linkdata.append(lout)

    chartdata = [{
            "id": nodedata[t]["id"] if v["direction"] == "in" else nodedata[s]["id"],
            "name": t if v["direction"] == "in" else s,
            "type": v["direction"],
            "gtype": gtype,
            "sum": nodedata[t]["weight"] if v["direction"] == "in" else nodedata[s]["weight"],
            "weight": v["weight"]
        } for s, t, v in links]

    return { "nodes": sorted(list(nodedata.values()), key=itemgetter("id")), "links": linkdata, "bars": chartdata }


def gen_flower_data(score_df, flower_prop, entity_names, flower_name,
                    coauthors, config=default_config):
    '''
    '''
    # Flower properties
    flower_type, leaves = flower_prop
    print("[gen_flower_data] flower_type", flower_type)

    print(datetime.now(), 'start score_leaves')
    entity_score = score_leaves(score_df, leaves)
    print(datetime.now(), 'finish score_leaves')

    # Ego name removal
    if (flower_type != 'conf'):
        entity_score = entity_score[~entity_score['entity_name'].str.lower()\
                .isin(entity_names)]

    # Self citation filter
    if not config['self_cite']:
        entity_score = entity_score[-entity_score['self_cite']]

    # Filter publication year for ego's paper
    filter_score = filter_year(entity_score, config['pub_lower'],
                                             config['pub_upper'])

    # Filter Citaiton year for reference links
    filter_score = filter_year(filter_score, config['cit_lower'],
                                             config['cit_upper'],
                                             index = 'influence_year')
    # print("[gen_flower_data] filter_score", filter_score)
    # Aggregate
    agg_score = agg_score_df(filter_score)

    # Get the top scores with filter considerations
    # Iteratively generates a top number of entries until filters get the right amount
    i = 0
    top_score = list()
    max_search = False
    num_leaves = config["num_leaves"]
    while len(top_score) < num_leaves and not max_search :
        top_score = agg_score.head(n=(4 + i) * num_leaves)

        if len(agg_score) == len(top_score):
            max_search = True

        # Get top scores for graph
        if (flower_type != 'conf'):
            top_score = top_score[ ~top_score['entity_name'].isin(entity_names) ]

        # Filter coauthors
        print(coauthors)
        if config['icoauthor']:
            top_score = flag_coauthor(top_score, coauthors)
        else:
            top_score = top_score[ ~top_score['entity_name'].isin(coauthors) ]

        top_score = top_score.head(n=num_leaves)
        top_score.ego = flower_name
        # Increase the search space
        i += 1

    # Get papers to show info for each node
    #print(datetime.now(), 'node_info')
    #node_info = select_node_info(filter_score, top_score['entity_name'].tolist())
    #print(datetime.now(), 'node_info')

    # Graph score
    graph_score = score_df_to_graph(top_score)

    # D3 format
    data = processdata(flower_type, graph_score, num_leaves, config['order'])

    return flower_type, data #, node_info
