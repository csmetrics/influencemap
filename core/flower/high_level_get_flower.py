from webapp.utils import progressCallback, resetProgress
from webapp.graph import processdata
import core.utils.entity_type as ent
from core.flower.draw_flower_test import draw_flower
from core.flower.flower_bloomer import getFlower, getPreFlowerData
from core.search.mag_flower_bloom import *
from core.utils.get_entity import entity_from_name

from core.search.query_paper     import paper_query
from core.search.query_paper_mag import paper_mag_query
from core.search.query_info      import paper_info_check_query, paper_info_mag_check_multiquery
from core.score.agg_paper_info   import score_paper_info_list

flower_leaves = { 'author': [ent.Entity_type.AUTH]
                , 'conf': [ent.Entity_type.CONF, ent.Entity_type.JOUR]
                , 'inst': [ent.Entity_type.AFFI]
    }

str_to_ent = {
        "author": ent.Entity_type.AUTH,
        "conference": ent.Entity_type.CONF,
        "journal": ent.Entity_type.JOUR,
        "institution": ent.Entity_type.AFFI
    }

def get_flower_data_high_level(entitytype, authorids, normalizedname, selection=None):

    min_year = None
    max_year = None

    # Get the selected paper
    selected_papers = list()
    if selection:
        # If selection is not None, they follow selection
        for eid in authorids:
            selected_papers += list(map(lambda x : x['eid'], selection[eid]))
    else:
        for eid in authorids:
            #papers = paper_query(str_to_ent[entitytype], eid)
            papers = paper_mag_query(str_to_ent[entitytype], eid) # API
            print(eid, str_to_ent[entitytype])
            print(papers)
            if papers:
                selected_papers += papers

    print()
    print('Number of Papers Found: ', len(selected_papers))
    print()

    # Turn selected paper into information dictionary list
    paper_information = paper_info_mag_check_multiquery(selected_papers) # API
    #for paper in selected_papers:
    #    paper_info = paper_info_check_query(paper)
    #    if paper_info:
    #        paper_information.append(paper_info)

    print()
    print('Number of Paper Information Found: ', len(paper_information))
    print()
    if not paper_information:
        return None

    # Generate score for each type of flower
    flower_score = [None, None, None]
    for i, flower_item in enumerate(flower_leaves.items()):
        name, leaves = flower_item

        entity_score = score_paper_info_list(paper_information, leaves)
        entity_score = entity_score[entity_score['entity_id'] != normalizedname]

        print(entity_score)

        agg_score = agg_score_df(entity_score, min_year, max_year)
        agg_score.ego = normalizedname[0]
        print(agg_score)

        score = score_df_to_graph(agg_score)
        print(score)

        flower_score[i] = score

    author_data = processdata("author", flower_score[0])
    conf_data = processdata("conf", flower_score[1])
    inst_data = processdata("inst", flower_score[2])

    return (author_data, conf_data, inst_data)


