import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import networkx as nx

# Config setup
from config import *

def draw_flower(egoG=None, ax=None, 
                   plot_setting={'max_marker':30, 'max_line': 4., 'min_line': .5, 
                                 "sns_palette": "RdBu", "out_palette": "Reds", "in_palette": "Blues", 
                                 "num_colors": 100, "delta_text":0.02}, filename=None):

    ps = plot_setting
    if not ax:
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111)

    sns.set_context("talk", font_scale=1.)
    sns.set_style("white")
    sns.despine()

    center_node = egoG.graph['ego']
        
    xroot = 0.
    yroot = 0.
    ax.plot(xroot, yroot, 'o', c=[.5, .5, .5], markersize=1.2*ps['max_marker'], fillstyle='full', mec='0.5')
    ax.text(xroot, yroot-5*ps['delta_text'], center_node, horizontalalignment='center')

    # Get basic node information from ego graph
    outer_nodes = list(egoG)
    outer_nodes.remove(center_node)
    outer_nodes.sort(key=lambda n : egoG.nodes[n]['weight'])

    num_clrs = 100
    dot_colors = sns.color_palette("RdBu", num_clrs)
    out_edge_color = dot_colors[round(3*num_clrs/4)] #{'r':32, 'g':32, 'b':192}
    in_edge_color = dot_colors[round(1*num_clrs/4)] #{'r':192, 'g':32, 'b':32}

    anglelist = np.linspace(np.pi, 0., num=NUM_LEAVES)
    n_outer_nodes = len(outer_nodes)

    for i, node in enumerate(outer_nodes):
        xp = np.cos(anglelist[i])
        yp = np.sin(np.abs(anglelist[i]))

        out_lw = ps['max_line'] * egoG[center_node][node]['weight'] + ps['min_line']
        in_lw = ps['max_line'] * egoG[node][center_node]['weight'] + ps['min_line']

        # draw connectors/arcs
        ax.annotate("", xy=(xroot, yroot), xycoords='data',
                xytext=(xp, yp), textcoords='data',
                arrowprops=dict(arrowstyle="-", #linestyle="dashed",
                                color=out_edge_color, linewidth=in_lw,
                                connectionstyle="arc3,rad=0.12", ), )

        ax.annotate("", xy=(xp, yp), xycoords='data',
                xytext=(xroot, yroot), textcoords='data',
                arrowprops=dict(arrowstyle="->", #linestyle="dashed",
                                color=in_edge_color, linewidth=out_lw,
                                connectionstyle="arc3,rad=0.12",),)

        # draw the node
        ax.plot(xp, yp, 'o', #c=dot_colors[int(ci)], markersize=int(sz), 
                alpha=.9, mec='0.5', mew=.5) 

        # Angle of text dependent on side of flower
        if i < n_outer_nodes / 2:
            text_angle = anglelist[i] - np.pi
        else:
            text_angle = anglelist[i]

        xt = xp * (1.06 + 0.0145 * (len(node) - 1))
        yt = yp * (1.06 + 0.0145 * (len(node) - 1))

        # Draw text
        ax.text(xt, yt, node, size=12,
            horizontalalignment='center',
            verticalalignment='center',
            rotation_mode='anchor',
            rotation=text_angle * 180.0 / np.pi)



    ax.set_xlim((-1.4, 1.4))
    ax.set_ylim((-.1, 1.3))
    ax.axis('off')
    if filename != None:
        plt.savefig(filename)
