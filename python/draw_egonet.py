
def draw_egocircle(graph=None, ego=None, ax=None, direction="out", renorm_weights='lin', 
                   plot_setting={'max_marker':30, 'max_line': 4., 'min_line': .5, 
                                 "sns_palette": "RdBu", "out_palette": "Reds", "in_palette": "Blues", 
                                 "num_colors": 100, "delta_text":0.02}):
    ps = plot_setting
    if not ax:
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111)
    sns.set_context("talk", font_scale=1.)
    sns.set_style("white")
    sns.despine()
        
    xroot = 0.
    yroot = 0.
    ax.plot(xroot, yroot, 'o', c=[.5, .5, .5], markersize=1.2*ps['max_marker'], fillstyle='full', mec='0.5')
    ax.text(xroot, yroot-5*ps['delta_text'], ego, horizontalalignment='center')
    
    
    # take the subgraph out as a node list and a weight list
    if direction == "in":
        node_list = [e[0] for e in graph.in_edges(ego)]
        if ego in node_list:
            node_list.remove(ego)
        weight_list = [graph[n][ego]['weight'] for n in node_list]
        node_colors = sns.color_palette(ps['in_palette'], ps['num_colors'])
        arrow_str = '->'
    else:
        node_list = [e[1] for e in graph.out_edges(ego)]
        if ego in node_list:
            node_list.remove(ego)
        weight_list = [graph[ego][n]['weight'] for n in node_list]
        node_colors = sns.color_palette(ps['out_palette'], ps['num_colors'])
        arrow_str = '<-'
    
    nn = len(node_list)
    edge_color = node_colors[int(ps['num_colors']/2)]
    
    # nomalise these weights to get edge width
    if renorm_weights == 'log':
        weight_max = max( [np.log10(w) for w in weight_list] )
        weight_min = min( [np.log10(w) for w in weight_list] )
        weight_norm = [ (np.log10(w)-weight_min)/(weight_max-weight_min) for w in weight_list ]
    elif renorm_weights == 'lin':
        weight_max = max(weight_list)
        weight_min = min(weight_list)
        weight_norm = [ (w-weight_min)/(weight_max-weight_min) for w in weight_list ]
    #print(weight_norm, weight_max, weight_min, nn)
    
    # sort order of edges based on the weight 
    isort = np.argsort(weight_list)[::-1]
        
    anglelist = np.linspace(0.05, np.pi, num=nn)
    #iangle = [i for i in range(0, nn, 2) ] + [i for i in range(nn - (nn+1)%2, 0, -2) ]
    #anglelist = anglelist[iangle]
    #print(iangle)
    node_pos = [()]* nn
    
    for i, jn in enumerate(isort):
        n = node_list[jn]
        w = weight_norm[jn]
        # node position
        xp = np.cos(anglelist[i]) + 1.
        yp = np.sin(np.abs(anglelist[i])) * ((-1)**(i%2))
        node_pos[jn] = (xp, yp)
        
        # calculate node color index based on its weight
        ci = int( w*(len(node_colors)-1e-3) )
        lw = ps['max_line'] * w + ps['min_line']
        # plot the node
        ax.plot(xp, yp, 'o', c=node_colors[ci], markersize= ps['max_marker'], # markersize=int(sz), 
            alpha=.9, mec='0.5', mew=.5) 
        # add node text 
        h = ax.text(xp, yp, n, horizontalalignment='left')
        # draw arc / arrow 
        ax.annotate("", xy=(xroot, yroot), xycoords='data',
            xytext=(xp, yp), textcoords='data',
            arrowprops=dict(arrowstyle = arrow_str, 
                        color=edge_color, linewidth = lw,
                        connectionstyle="arc3,rad=0.12", ), )
        
    # now draw the remaining edges of the ego net, between pairs of neighbours
    for i, j in itertools.permutations([i for i in range(nn)], r=2):
        # draw edge if exists
        if node_list[j] in graph[node_list[i]]:
            w = graph[node_list[i]][node_list[j]]['weight']
            lw = ps['max_line'] * w + ps['min_line']

            ax.annotate("", xy = node_pos[i], xycoords='data',
                xytext = node_pos[j], textcoords='data',
                arrowprops=dict(arrowstyle="-", #linestyle="dashed",
                                color = (.5, .5, .5), linewidth= lw,
                                connectionstyle="arc3,rad=0.12", ), )
    
    # TODO: colorbar scale
    #cbar = plt.colorbar(cax = ax) #, ticks=[-1, 0, 1])
    #cbar.ax.set_yticklabels(['< -1', '0', '> 1'])  # vertically oriented colorbar
   
    ax.set_xlim((-.2, 2.2))
    ax.set_ylim((-1.1, 1.1))
    ax.axis('off')

    
def draw_halfcircle(graph=None, ego=None, ax=None, direction="out", renorm_weights='lin', 
                   plot_setting={'max_marker':30, 'max_line': 4., 'min_line': .5, 
                                 "sns_palette": "RdBu", "out_palette": "Reds", "in_palette": "Blues", 
                                 "num_colors": 100, "delta_text":0.02}):
    ps = plot_setting
    if not ax:
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111)
    sns.set_context("talk", font_scale=1.)
    sns.set_style("white")
    sns.despine()
        
    xroot = 0.
    yroot = 0.
    ax.plot(xroot, yroot, 'o', c=[.5, .5, .5], markersize=1.2*ps['max_marker'], fillstyle='full', mec='0.5')
    ax.text(xroot, yroot-5*ps['delta_text'], ego, horizontalalignment='center')
    
    
    # take the subgraph out as a node list and a weight list
    if direction == "in":
        node_list = [e[0] for e in graph.in_edges(ego)]
        if ego in node_list:
            node_list.remove(ego)
        weight_list = [graph[n][ego]['weight'] for n in node_list]
        node_colors = sns.color_palette(ps['in_palette'], ps['num_colors']) #len(node_list))
        arrow_str = '->'
    else:
        node_list = [e[1] for e in graph.out_edges(ego)]
        if ego in node_list:
            node_list.remove(ego)
        weight_list = [graph[ego][n]['weight'] for n in node_list]
        node_colors = sns.color_palette(ps['out_palette'], ps['num_colors'])
        arrow_str = '<-'
    
    nn = len(node_list)
    edge_color = node_colors[int(ps['num_colors']/2)]
    
    # nomalise these weights to get edge width
    if renorm_weights == 'log':
        weight_max = max( [np.log10(w) for w in weight_list] )
        weight_min = min( [np.log10(w) for w in weight_list] )
        weight_norm = [ (np.log10(w)-weight_min)/(weight_max-weight_min) for w in weight_list ]
    elif renorm_weights == 'lin':
        weight_max = max(weight_list)
        weight_min = min(weight_list)
        weight_norm = [ (w-weight_min)/(weight_max-weight_min) for w in weight_list ]
    print(weight_norm, weight_max, weight_min, nn)
    
    # sort order of edges based on the weight 
    isort = np.argsort(weight_list)
    
    anglelist = np.linspace(np.pi, 0., num=nn)
    iangle = [i for i in range(0, nn, 2) ] + [i for i in range(nn - (nn+1)%2, 0, -2) ]
    #anglelist = anglelist[iangle]
    #print(iangle)
    
    for i, jn in enumerate(isort):
        n = node_list[jn]
        w = weight_norm[jn]
        # node position
        xp = np.cos(anglelist[i]) 
        yp = np.sin(np.abs(anglelist[i])) 
        #print((xp, yp))
        
        # calculate node color index based on its weight
        ci = int( w*(len(node_colors)-1e-3) )
        lw = ps['max_line'] * w + ps['min_line']
        # plot the node
        ax.plot(xp, yp, 'o', c=node_colors[ci], markersize= ps['max_marker'], # markersize=int(sz), 
            alpha=.9, mec='0.5', mew=.5) 
        # add node text 
        h = ax.text(xp, yp, n, horizontalalignment='left')
        # draw arc / arrow 
        ax.annotate("", xy=(xroot, yroot), xycoords='data',
            xytext=(xp, yp), textcoords='data',
            arrowprops=dict(arrowstyle = arrow_str, 
                        color=edge_color, linewidth = lw,
                        connectionstyle="arc3,rad=0.12", ), )
        
    ### TODO: draw color bar
    #cbar = plt.colorbar(cax = ax) #, ticks=[-1, 0, 1])
    #cbar.ax.set_yticklabels(['< -1', '0', '> 1'])  # vertically oriented colorbar
   
    ax.set_xlim((-1.2, 1.2))
    ax.set_ylim((-.1, 1.1))
    ax.axis('off')
    