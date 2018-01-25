import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import networkx as nx
import math
from datetime import datetime
from matplotlib import rc

# Config setup
from config import *

def draw_flower(egoG=None, ax=None, 
                   plot_setting={'max_marker':30, 'max_line': 4., 'min_line': .5, 
                                 "sns_palette": "RdBu", "out_palette": "Reds", "in_palette": "Blues", 
                                 "num_colors": 200, "delta_text":0.02}, filename=None):

    print('{} start drawing flower\n---'.format(datetime.now()))

    ps = plot_setting
    if not ax:
        fig = plt.figure(figsize=(16, 8))
        ax = fig.add_subplot(111)

    sns.set_context("talk", font_scale=1.)
    sns.set_style("white")
    sns.despine()

    # Get center node string
    center_node = egoG.graph['ego']
        
    xroot = 0.
    yroot = 0.
    ax.plot(xroot, yroot, 'o', c=[.5, .5, .5], markersize=1.2*ps['max_marker'], fillstyle='full', mec='0.5')

    # Get basic node information from ego graph
    outer_nodes = list(egoG)
    outer_nodes.remove(center_node)
    outer_nodes.sort(key=lambda n : egoG.nodes[n]['ratiow'])

    # Colours
    dot_colors = sns.color_palette("RdBu", ps['num_colors'])
    out_edge_color = dot_colors[round(3*ps['num_colors']/4)] #{'r':32, 'g':32, 'b':192}
    in_edge_color = dot_colors[round(1*ps['num_colors']/4)] #{'r':192, 'g':32, 'b':32}

    anglelist = np.linspace(np.pi, 0., num=NUM_LEAVES)
    n_outer_nodes = len(outer_nodes)

    for i, node in enumerate(outer_nodes):
        xp = np.cos(anglelist[i])
        yp = np.sin(np.abs(anglelist[i]))

        out_lw = ps['max_line'] * egoG[center_node][node]['nweight'] + ps['min_line']
        in_lw = ps['max_line'] * egoG[node][center_node]['nweight'] + ps['min_line']

        size = egoG.nodes[node]['sumw'] * ps['max_marker'] / 2 + ps['max_marker'] / 2
        colour = egoG.nodes[node]['nratiow'] * (ps['num_colors'] - 1)

        # draw connectors/arcs
        ax.annotate("", xy=(xroot, yroot), xycoords='data',
                xytext=(xp, yp), textcoords='data',
                arrowprops=dict(arrowstyle="-", #linestyle="dashed",
                                color=out_edge_color, linewidth=in_lw,
                                connectionstyle="arc3,rad=0.22", ), )

        ax.annotate("", xy=(xp, yp), xycoords='data',
                xytext=(xroot, yroot), textcoords='data',
                arrowprops=dict(arrowstyle="->", #linestyle="dashed",
                                color=in_edge_color, linewidth=out_lw,
                                connectionstyle="arc3,rad=0.22",),)

        # Plot style for coauthors
        if egoG.nodes[node]['coauthor']:
            weight='medium'
            node_mec = 'g'
            node_mew = 2.0
        else:
            weight = 'normal'
            node_mec = '0.5'
            node_mew = 1

        # draw the node
        ax.plot(xp, yp, 'o', markersize=int(size), c=dot_colors[int(colour)],
                alpha=.9, mec=node_mec, mew=node_mew) 

        # Angle of text dependent on side of flower
        if i < n_outer_nodes / 2:
            text_angle = anglelist[i] - np.pi
        else:
            text_angle = anglelist[i]

        # name split in words
        words = node.split() if node != None else ["None"]

        # Position of text
        xt = xp * (1.1 + 0.01 * (max(map(len, words)) - 1))
        yt = yp * (1.1 + 0.01 * (max(map(len, words)) - 1))

        # values to determin how to space word/name
        if len(words) > 1:
            word_split = len(words) / 2
            floor_len = max(sum(map(len, words[:math.floor(word_split)])), sum(map(len, words[math.floor(word_split):])))
            ceil_len = max(sum(map(len, words[:math.ceil(word_split)])), sum(map(len, words[math.ceil(word_split):])))

            if floor_len < ceil_len:
                text = ' '.join(words[:math.floor(word_split)]) + '\n' + ' '.join(words[math.floor(word_split):])

            else:
                text = ' '.join(words[:math.ceil(word_split)]) + '\n' + ' '.join(words[math.ceil(word_split):])
        else:
            text = words[0]

        # Draw text
        ax.text(xt, yt, text, size=15,
            weight=weight,
            horizontalalignment='center',
            verticalalignment='center',
            rotation_mode='anchor',
            rotation=text_angle * 180.0 / np.pi)

    # Label flower center
    ax.text(xroot, yroot-0.08, center_node, horizontalalignment='center', verticalalignment='center', size=20)
    ax.text(xroot, yroot-0.13, 'Flower Type: ' + egoG.graph['mapping'], horizontalalignment='center', verticalalignment='center', size=10)
    ax.text(xroot, yroot-0.17, 'Publication Dates: ' + egoG.graph['date_range'], horizontalalignment='center', verticalalignment='center', size=10)

    ax.set_xlim((-1.2, 1.2))
    ax.set_ylim((-.05, 1.15))
    ax.axis('off')

    if filename != None:
        plt.savefig(filename)

    plt.close()

    print('{} finish drawing flower\n---'.format(datetime.now()))

def draw_cite_volume(egoG=None, ax=None, filename=None):
    if not ax:
        fig = plt.figure(figsize=(15, 4))
        ax = fig.add_subplot(111)

    center_node = egoG.graph['ego']

    # Get basic node information from ego graph
    outer_nodes = list(egoG)
    outer_nodes.remove(center_node)
    outer_nodes.sort(key=lambda n : egoG.nodes[n]['ratiow'])

    # x position
    x_pos = [x + 1 for x in range(len(outer_nodes))]

    v_bar_influencing = ax.bar([x - 0.2 for x in x_pos], [egoG[center_node][node]['weight'] for node in outer_nodes], width=.4) #, color=bar_colrs3[mdx])
    ax.set_ylim([0, max(egoG.graph['max_influencing'], egoG.graph['max_influenced'])])

    ax2 = ax.twinx()
    v_bar_influencing = ax.bar([x + 0.2 for x in x_pos], [egoG[node][center_node]['weight'] for node in outer_nodes], width=.4) #, color=bar_colrs3[mdx])
    ax2.set_ylim([0, max(egoG.graph['max_influencing'], egoG.graph['max_influenced'])])

    tk2 = plt.xticks([],[])
    ax.set_xticks(x_pos)
    ax.set_xticklabels(list(map(lambda x : x[:10], outer_nodes)), rotation=90)

    ax.set_ylabel('reference score')#, color=bar_colrs3[mdx])
    ax2.set_ylabel('citation score')#, color=bar_colrs2[mdx])

    # plot info on left bot
    fig.text(0, 0, 'Pub Dates: ' + egoG.graph['date_range'], horizontalalignment='left', verticalalignment='bottom', size=10)
    fig.text(0, 0 + 0.035, 'Flower Type: ' + egoG.graph['mapping'], horizontalalignment='left', verticalalignment='bottom', size=10)
    fig.text(0, 0 + 0.07, 'Ego: ' + center_node, horizontalalignment='left', verticalalignment='bottom', size=10)
    
    #for tl in ax.get_yticklabels():
    #    tl.set_color(bar_colrs3[mdx])
    #for tl in ax2.get_yticklabels():
    #    tl.set_color(bar_colrs2[mdx]) 
    plt.tight_layout()

    if filename != None:
        plt.savefig(filename)

    plt.close()
