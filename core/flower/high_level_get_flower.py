from webapp.graph                  import processdata
from core.flower.draw_flower_test  import draw_flower
from core.utils.get_entity         import entity_from_name
from core.search.query_paper       import paper_query
from core.search.query_paper_mag   import paper_mag_multiquery
from core.search.query_info        import paper_info_check_query, paper_info_mag_check_multiquery
from core.score.agg_paper_info     import score_paper_info_list, score_leaves
from core.score.agg_score          import agg_score_df, agg_node_info
from core.score.agg_utils          import get_coauthor_mapping
from core.score.agg_utils          import flag_coauthor
from core.score.agg_filter         import filter_year
from core.flower.flower_bloom_data import score_df_to_graph
from core.utils.get_stats          import get_stats
from core.config                   import *

from datetime    import datetime
from collections import Counter
from operator    import itemgetter

import core.utils.entity_type as ent

flower_leaves = [ ('author', [ent.Entity_type.AUTH])
                , ('conf'  , [ent.Entity_type.CONF, ent.Entity_type.JOUR])
                , ('inst'  , [ent.Entity_type.AFFI]) ]

str_to_ent = {
        "author": ent.Entity_type.AUTH,
        "conference": ent.Entity_type.CONF,
        "journal": ent.Entity_type.JOUR,
        "institution": ent.Entity_type.AFFI
    }

default_config = {
        'self_cite': True,
        'icoauthor': True,
        'pub_lower': None,
        'pub_upper': None,
        'cit_lower': None,
        'cit_upper': None,
        }


def gen_flower_data(score_df, flower_prop, entity_names, flower_name,
                    coauthors, config=default_config):
    '''
    '''
    # Flower properties
    flower_type, leaves = flower_prop

    print(datetime.now(), 'score_leaves')
    entity_score = score_leaves(score_df, leaves)
    print(datetime.now(), 'score_leaves')

    # Ego name removal
    if (flower_type != 'conf'):
        entity_score = entity_score[~entity_score['entity_name'].str.lower()\
                .isin(entity_names)]

    # Self citation filter
    if not config['self_cite']:
        entity_score = entity_score[~entity_score['self_cite']]

    # Filter publication year for ego's paper
    filter_score = filter_year(entity_score, config['pub_lower'],
                                             config['pub_upper'])

    # Filter Citaiton year for reference links
    filter_score = filter_year(filter_score, config['cit_lower'],
                                             config['cit_upper'],
                                             index = 'influence_year')

    # Aggregate
    agg_score = agg_score_df(filter_score)

    # Get the top scores with filter considerations
    # Iteratively generates a top number of entries until filters get the right amount
    i = 0
    top_score = list()
    max_search = False
    while len(top_score) < NUM_LEAVES and not max_search :
        top_score = agg_score.head(n=(4 + i) * NUM_LEAVES)

        if len(agg_score) == len(top_score):
            max_search = True

        # Get top scores for graph
        if (flower_type != 'conf'):
            top_score = top_score[ ~top_score['entity_name'].isin(entity_names) ]

        # Filter coauthors
        if config['icoauthor']:
            top_score = flag_coauthor(top_score, coauthors)
        else:
            top_score = agg_score[ ~top_score['entity_name']\
                                    .isin(coauthors) ]

        top_score = top_score.head(n=NUM_LEAVES)
        top_score.ego = flower_name
        # Increase the search space
        i += 1


    # Graph score
    graph_score = score_df_to_graph(top_score)

    # Generate node information
    #node_info = agg_node_info(filter_score, agg_score['entity_name'])

    # D3 format
    data = processdata(flower_type, graph_score)

    return flower_type, data, top_score['entity_name'].tolist()
