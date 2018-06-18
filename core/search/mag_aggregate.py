import sqlite3
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

# Generates pandas dataframe for scores
def agg_score_df(influence_df, coauthors=set([]), \
    score_year_min=None, score_year_max=None, \
    ratio_func=np.vectorize(lambda x, y : y - x), sort_func=np.maximum):

    print('\n---\n{} start score generation'.format(datetime.now()))

    # Check if any range set
    if score_year_min == None and score_year_max == None:
        score_df = influence_df
    else:
        no_nan_date = influence_df[ influence_df['influence_date'].notna() ]

        # Set minimum year if none set
        if score_year_min == None:
            score_date_min = no_nan_date['influence_date'].min()
        else:
            score_date_min = min(no_nan_date['influence_date'].max(),\
                datetime(max(score_year_min, 1), 1, 1))
            

        # Set maximum year if none set
        if score_year_max == None:
            score_date_max = no_nan_date['influence_date'].max()
        else:
            score_date_max = max(no_nan_date['influence_date'].min(),\
                datetime(max(score_year_max, 1), 1, 1))

        # Filter based on year
        score_df = no_nan_date[(score_date_min <= \
            no_nan_date['influence_date']) & \
            (no_nan_date['influence_date'] <= score_date_max)]

    # Remove year column
    score_df = score_df[['entity_id', 'influenced', 'influencing']]

    # Aggrigatge scores up
    score_df = score_df.groupby('entity_id').agg(np.sum).reset_index()

    # calculate sum
    score_df['sum'] = score_df['influenced'] + score_df['influencing']

    # calculate influence ratios
    score_df['ratio'] = ratio_func(score_df['influenced'], score_df['influencing'])

    # sort by union max score
    score_df = score_df.assign(tmp = sort_func(score_df['influencing'], score_df['influenced']))
    score_df = score_df.sort_values('tmp', ascending=False).drop('tmp', axis=1)

    # Flag coauthors TODO FIX
    score_df['coauthor'] = False

    print('{} finish score generation\n---'.format(datetime.now()))

    return score_df


if __name__ == '__main__':
    import entity_type as ent
    from mag_interface import *
    
    name = sys.argv[1]
    paper_map = auth_name_to_paper_map(name)
    citation_score = paper_id_to_citation_score(paper_map, ent.Entity_type.AUTH)
    reference_score = paper_id_to_reference_score(paper_map, ent.Entity_type.AUTH)
    score_df = gen_score_df(citation_score, reference_score)
    score = score_entity(score_df, ent.Entity_map(ent.Entity_type.AUTH, [ent.Entity_type.AUTH]))

    agg_score = agg_score_df(score, ent.Entity_map(ent.Entity_type.AUTH, [ent.Entity_type.AUTH]), '')
    print(agg_score)
    # print(agg_score[agg_score['coauthor']])
