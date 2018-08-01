'''
Functions to format the standard plots
'''

import seaborn as sns


def cmp_plot(cmp_matrix, labels, plt):
    ''' Plots a comparison matrix as a heatmap in seaborn.
    '''
    ax = sns.heatmap(cmp_matrix, annot=True)
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)

    plt.setp(ax.get_xticklabels(), rotation=90, ha="right",
                     rotation_mode="anchor")
    plt.setp(ax.get_yticklabels(), rotation=0, ha="right",
                     rotation_mode="anchor")

    return ax
