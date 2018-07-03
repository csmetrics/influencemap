'''
Various filter functions used to restrict the rows of the scoring dataframe
before aggregation.

date:   03.07.18
author: Alexander Soen
'''

def filter_year(influence_df, score_year_min, score_year_max,
                index='publication_year'):
    ''' Filters based on the year of the interested entity's papers.
    '''

    # Check if any range set
    if score_year_min == None and score_year_max == None:
        return influence_df
    else:
        no_nan_date = influence_df[ influence_df[index].notna() ]

        # Set minimum year if none set
        if score_year_min == None:
            score_date_min = no_nan_date[index].min()
        else:
            score_date_min = min(no_nan_date[index].max(),\
                score_year_min)

        # Set maximum year if none set
        if score_year_max == None:
            score_date_max = no_nan_date[index].max()
        else:
            score_date_max = max(no_nan_date[index].min(),\
                score_year_max)

        # Filter based on year
        return no_nan_date[(score_date_min <= no_nan_date[index]) & \
                           (no_nan_date[index] <= score_date_max)]
