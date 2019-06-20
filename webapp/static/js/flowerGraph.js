var colormaps = [
  d3.interpolateRdBu,
  d3.interpolatePiYG,
  d3.interpolatePuOr,
  d3.interpolatePRGn,
  d3.interpolateBrBG,
  d3.interpolateRdGy,
  d3.interpolateRdYlBu,
  d3.interpolateRdYlGn,
  d3.interpolateSpectral,
];

// var colors = colormaps[parseInt(Math.random()*colormaps.length)];
var colors = colormaps[0];
var selcolor = [colors(0.2), colors(0.8)],
    norcolor = [colors(0.25), colors(0.75)],
    hidcolor = [colors(0.4), colors(0.6)];

var width, height, center, magf;
var link = [], flower_split = [], bar = [], numnodes = [], cnode = [], 
    svg = [], bar_axis_x = [], bar_axis_y = [], node_out = [], text_out = [],
    data_arr = [], ref_node = [], ref_link = [], node_g_arr = [], link_g_arr
    = [];
var node_max_area = 1000.0;

function drawLegend() {
  var colorScale = d3.scaleSequential(colors).domain([0, 500]);
  var svg = d3.select("#flower-legend")
    .append("svg")
    .attr("width", 700)
    .attr("height", 15)
    .append("g");
  var bars = svg.selectAll(".bars")
    .data(d3.range(700), function(d) { return d; })
  .enter().append("rect")
    .attr("class", "bars")
    .attr("x", function(d, i) { return i; })
    .attr("y", 0)
    .attr("height", 15)
    .attr("width", 1)
    .style("fill", function(d, i ) { return colorScale(d); })
}

function drawFlower(svg_id, data, idx, w, num, order) {
    var compare_ref = referenceCheckbox.checked;

    var total_entity_num = data["total"];
    var nodes = data["nodes"];
    var links = data["links"];
    var bars = data["bars"];

    data_arr[idx] = data;

    window_scaling_factor = w/1000

    v_margin = 150-(Math.max(5, nodes.length-15)*3);
    yheight = 120-Math.max(20, nodes.length-15);

    svg[idx] = d3.select(svg_id),
    width = w, magf = Math.min(250, width/5),
    height = 600,
    numnodes[idx] = nodes.length,
    center = [width*0.45, height*0.6];
    flower_split[idx] = false;

    // Ordering
    var ordering = reorder(num, order, data);
        [xpos, ypos] = gen_pos(num);

    // bar location
    bar_width_ratio = 0.6,
    bar_right_margin = 0,
    bar_left = center[0] - width * bar_width_ratio /2
    bar_right = center[0] + width * bar_width_ratio /2

    var x = d3.scaleBand()
              .range([bar_left, bar_right])
              .padding(0.1);
    var y = d3.scaleLinear()
              .range([yheight, 0]);
    x.domain(bars.map(function(d) { return d.name; }));
    y.domain([0, d3.max(bars, function(d) { return d.weight; })]);

    // bar chart
    bar[idx] = svg[idx].append("g").selectAll("rect")
        .data(bars)
      .enter().append("rect")
        .attr("class", "bar")
        .attr("id", function(d) { return d.id; })
        .attr("name", function(d) { return d.name; })
        .attr("x", function(d) { if (d.type == "out") return x(d.name)+x.bandwidth()/2; else return x(d.name); })
        .attr("y", function(d) { return y(d.weight)-v_margin; })
        .attr("width", x.bandwidth()/2)
        .attr("height", function(d) { return yheight - y(d.weight); })
        .attr("transform", "translate(0," + height + ")")
        .style("opacity", 1)
        .style("fill", barColour);

    // bar chart x axis
    bar_axis_x[idx] = svg[idx].append("g")
        .attr("transform", "translate(0," + (height+yheight-v_margin) + ")")
        .call(d3.axisBottom(x))
        .selectAll("text")
          .text(function(d, i) { return barText(idx, d); })
          .attr("id", function(d, i) { return i+1; })
          .attr("name", function(d, i) { return d; })
          .attr("class", "hl-bar-text node-text")
          .style("text-anchor", "end")
          .attr("dx", "-.8em")
          .attr("dy", function() {return - x.bandwidth()/15-5; } )//"-3px")
          .attr("transform", "rotate(-90)")
          .style("visibility", "hidden");

    // bar chart x axis title
    var graph_types = ["authors", "venues", "institutions", "topics"];
    var top_numbers = Math.min(50, total_entity_num);
    svg[idx].append("text")
      .attr("transform", "translate(" + (width/2)+ "," +(20+height+yheight-v_margin) + ")")
      // .attr("transform", "translate(" + (width/2)+ "," +(20+height-v_margin) + ")")
      .style("text-anchor", "start")
      .text("Top "+top_numbers+" of total "+total_entity_num+" "+graph_types[idx]);

    // bar chart y axis
    bar_axis_y[idx] = svg[idx].append("g")
        .attr("transform", "translate(" + bar_left + "," + (height-v_margin) + ")")
        .call(d3.axisLeft(y).ticks(5));


    // flower graph edge arrow
    svg[idx].append("defs").selectAll("marker")
        .data(links)
      .enter().append("marker")
        .attr("id", function(d) { return d.gtype+"_"+d.type+"_"+d.id; })
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", function (d) { return Math.max(9, nodeRadius(d.padding)/window_scaling_factor); })
        .attr("refY", function (d) { return -d.padding; })
        .attr("markerWidth", function (d) { return window_scaling_factor*arrow_size_calc(d.weight); })
        .attr("markerHeight", function (d) { return window_scaling_factor*arrow_size_calc(d.weight); })
        .attr("markerUnits", "userSpaceOnUse")
        .attr("orient", "auto")
      .append("path")
        .attr("d", "M0,-5L10,0L0,5")
        .style("fill", function (d) { if (d.type == "in") return norcolor[0]; else return norcolor[1]; });

    // flower graph edge arrow _selected
    svg[idx].append("defs").selectAll("marker")
        .data(links)
      .enter().append("marker")
        .attr("id", function(d) { return d.gtype+"_"+d.type+"_"+d.id+"_selected"; })
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", function (d) { return Math.max(9, nodeRadius(d.padding)/window_scaling_factor); })
        .attr("refY", function (d) { return -d.padding; })
        .attr("markerWidth", function (d) { return window_scaling_factor*arrow_size_calc(d.weight); })
        .attr("markerHeight", function (d) { return window_scaling_factor*arrow_size_calc(d.weight); })
        .attr("markerUnits", "userSpaceOnUse")
        .attr("orient", "auto")
      .append("path")
        .attr("d", "M0,-5L10,0L0,5")
        .style("fill", function (d) { if (d.type == "in") return selcolor[0]; else return selcolor[1]; });

    link_g = link_g_arr[idx] = svg[idx].append("g");
    node_g = node_g_arr[idx] = svg[idx].append("g");
    new_link_g = svg[idx].append("g");
    new_node_g = svg[idx].append("g");
    text_g = svg[idx].append("g");

    // flower graph nodes
    ref_node[idx] = node_out[idx] = node_g.selectAll("circle .hl-circle")
        .data(nodes)
      .enter().append("circle")
        .attr("id", function(d) { return d.id; })
        .attr("name", function(d) { return d.name; })
        .attr("class", "hl-circle")
        .attr("xpos", function(d) {
          if (ordering[d.id] == undefined) return center[0];
          else return center[0]+magf*xpos[ordering[d.id]]; })
        .attr("ypos", function(d) {
          if (ordering[d.id] == undefined) return center[1];
          else return center[1]-magf*ypos[ordering[d.id]]; })
        .attr("cx", function(d) {
          if (d.id > 0) return center[0];
          else return center[0]; })
        .attr("cy", function(d) {
          if (d.id > 0) return center[1]-magf;
          else return center[1]; })
        .attr("gtype", function(d) { return d.gtype; })
        .attr("r", function(d) { return nodeRadius(d.size);})//(node_min+node_scale*Math.sqrt(d.size)/Math.max(15, numnodes[idx]))*window_scaling_factor; })
        .style("fill", function (d, i) {
          if (d.id == 0) return "#fff";
          else if (compare_ref) return "#ddd"; else return colors(d.weight); })
        .style("stroke", function (d, i) {
          if (compare_ref) return "#ddd"; else return "black";})
        .style("stroke-width", 0.5)
        .style("cursor", "pointer")
        .style("visibility", function(d) {
          if (d.bloom_order > num) return "hidden";
          else return "visible"; })
        .style("opacity", function(d) {
          if (d.bloom_order > num) return 0.0;
          else return 1.0; })
        .on("mouseover", function() { highlight_on(idx, this, compare_ref); })
        .on("mouseout", function() { highlight_off(idx, compare_ref); })
        .on("click", function(d) { if (d.id != 0) { showNodeData(idx, this);} })
      .transition()
        .duration(2000)
        .attr("cx", function(d) {
          if (ordering[d.id] == undefined) return center[0];
          else return center[0]+magf*xpos[ordering[d.id]]; })
        .attr("cy", function(d) {
          if (ordering[d.id] == undefined) return center[1];
          else return center[1]-magf*ypos[ordering[d.id]]; })

    if (compare_ref) {
      // flower graph nodes - new node size
      node_out[idx] = new_node_g.selectAll("circle .hl-circle-new")
          .data(nodes)
        .enter().append("circle")
          .attr("id", function(d) { return d.id; })
          .attr("name", function(d) { return d.name; })
          .attr("class", "hl-circle-new")
          .attr("xpos", function(d) {
            if (ordering[d.id] == undefined) return center[0];
            else return center[0]+magf*xpos[ordering[d.id]]; })
          .attr("ypos", function(d) {
            if (ordering[d.id] == undefined) return center[1];
            else return center[1]-magf*ypos[ordering[d.id]]; })
          .attr("cx", function(d) {
            if (d.id > 0) return center[0];
            else return center[0]; })
          .attr("cy", function(d) {
            if (d.id > 0) return center[1]-magf;
            else return center[1]; })
          .attr("gtype", function(d) { return d.gtype; })
          .attr("r", function(d) {
            if (d.new_size >= 0 || d.id == 0) return nodeRadius(d.new_size);
            else return 0})
          .style("fill", function (d, i) {if (d.id == 0) return "#fff"; else return colors(d.new_weight);})
          .style("stroke", "black")
          .style("stroke-width", 0,5)
          .style("cursor", "pointer")
          .style("visibility", function(d) {
            if (d.bloom_order > num) return "hidden";
            else return "visible"; })
          .style("opacity", function(d) {
            if (d.bloom_order > num) return 0.0;
            else return 1.0; })
          .on("mouseover", function() { highlight_on(idx, this, compare_ref); })
          .on("mouseout", function() { highlight_off(idx, compare_ref); })
          .on("click", function(d) { if (d.id != 0) { showNodeData(idx, this);} })
        .transition()
          .duration(2000)
          .attr("cx", function(d) {
            if (ordering[d.id] == undefined) return center[0];
            else return center[0]+magf*xpos[ordering[d.id]]; })
          .attr("cy", function(d) {
            if (ordering[d.id] == undefined) return center[1];
            else return center[1]-magf*ypos[ordering[d.id]]; })
    }

    // flower graph node text
    text_out[idx] = text_g.selectAll("text")
        .data(nodes)
      .enter().append("text")
        .attr("id", function(d) { return d.id; })
        .attr("class", function(d) { if (d.id == 0) return 'hl-text node-ego-text'; else return 'hl-text node-text'; })
        .attr("gtype", function(d) { return d.gtype; })
        .attr("x", function(d) {
          if (ordering[d.id] == undefined) return center[0]
          else return text_order_xpos(d, xpos, ordering); })
        .attr("y", function(d) {
          if (ordering[d.id] == undefined) return center[1]
          else return text_order_ypos(d, xpos, ypos, num, ordering); })
        .attr("text-anchor", function(d) { return text_order_anchor(d, xpos, ordering); })
        .text(function(d) { return capitalizeString(d.gtype, d.name); })
        .style("fill", function(d) { if (d.coauthor == 'False') return "black"; else return "gray"; })
        .attr("node_size", function(d) { return d.size; })
        .style("visibility", function(d) {
          if (d.bloom_order > num) return "hidden";
          else return "visible";
        })
        .style("opacity", 0.0)
      .transition()
        .duration(2000)
        .style("opacity", function(d) {
          if (d.bloom_order > num) return 0.0;
          else return 1.0; })

    // flower graph edges
    ref_link[idx] = link[idx] = link_g.selectAll("path .link")
        .data(links)
      .enter().append("path")
        .attr("id", function(d) { return d.id; })
        .attr("d", function(d) { return linkArc(idx, d, false); })
        .attr("gtype", function(d) { return d.gtype; })
        .attr("class", function(d) { return "link " + d.type; })
        .attr('marker-end', function(d) {
          if (!compare_ref) return "url(#" + d.gtype+"_"+d.type+"_"+d.id + ")"; })
        .attr("type", function(d) {d.type})
        .style("stroke-width", function (d) { return window_scaling_factor*arrow_width_calc(d.weight); })
        .style("stroke", function (d) {
          if (compare_ref) return "#ddd";
          else if (d.type == "in") return norcolor[0]; else return norcolor[1]; })
        .style("visibility", function(d) {
          if (d.bloom_order > num) return "hidden";
          else return "visible"; })
        .style("opacity", function(d) {
          if (d.bloom_order > num) return 0.0;
          else return 1.0; })
      .transition()
        .duration(2000)
        .attr("d", function(d){ return linkArc(idx, d, true); })

    if (compare_ref) {
      // flower graph edges - new
      link[idx] = new_link_g.selectAll("path .new-link")
          .data(links)
        .enter().append("path")
          .attr("id", function(d) { return d.id; })
          .attr("d", function(d) { return linkArc(idx, d, false); })
          .attr("gtype", function(d) { return d.gtype; })
          .attr("class", function(d) { return "new-link " + d.type; })
          .attr('marker-end', function(d) {
            if (d.new_weight > 0) return "url(#" + d.gtype+"_"+d.type+"_"+d.id + ")"; })
          .attr("type", function(d) {d.type})
          .style("stroke-width", function (d) {
            if (d.new_weight > 0) return window_scaling_factor*arrow_width_calc(d.new_weight);
            else return 0 })
          .style("stroke", function (d) {
            if (d.type == "in") return norcolor[0];
            else return norcolor[1]; })
          .style("visibility", function(d) {
            if (d.bloom_order > num) return "hidden";
            else return "visible"; })
          .style("opacity", function(d) {
            if (d.bloom_order > num) return 0.0;
            else return 1.0; })
        .transition()
          .duration(2000)
          .attr("d", function(d){ return linkArc(idx, d, true); })
    }

    for (var bar_index = 0; bar_index < bar[idx]["_groups"][0].length; bar_index++) {
        var bname = bar[idx]["_groups"][0][bar_index].getAttribute("name");
        if ($("circle[name='"+bname+"']")[0] == undefined)
          bar[idx]["_groups"][0][bar_index].style = "fill:#ddd"
    }
}

function highlight_on(idx, selected, compare_ref) {
  id = d3.select(selected).attr("id");
  name = d3.select(selected).attr("name");
  group = d3.select(selected).attr("gtype");
  if (id == 0) return;

  // highlight rectangles
  svg[idx].selectAll("rect").each(function() {
    if (d3.select(this).attr("class") == "bar") {
        d3.select(this).style("opacity", function (d) {
          if(name != d.name && d.id != 0 && group == d.gtype)
            return 0.4;
          else return 1; });
    }
  });

  // highlight bar text
  svg[idx].selectAll("text").each(function() {
    if (d3.select(this).classed("hl-bar-text")) {
        d3.select(this).style("opacity", function () { if(name != this.getAttribute("name")) return 0.4; else return 1; });
    }
  });

  // highlight text
  svg[idx].selectAll("text").each(function() {
    if (d3.select(this).classed("hl-text")) {
        d3.select(this).style("opacity", function () { if(id != this.id) return 0.4; else return 1; });
    }
  });

  // highlight circles
  if (compare_ref) {
    svg[idx].selectAll("circle").each(function() {
      if (d3.select(this).attr("class") == "hl-circle-new") {
          d3.select(this).style("opacity", function (d) { if(id != d.id && d.id != 0 && group == d.gtype) return 0.4; else return 1; });
      }
    });
  } else {
    svg[idx].selectAll("circle").each(function() {
      if (d3.select(this).attr("class") == "hl-circle") {
          d3.select(this).style("opacity", function (d) { if(id != d.id && d.id != 0 && group == d.gtype) return 0.4; else return 1; });
      }
    });
  }

  if (compare_ref) {
    svg[idx].selectAll(".new-link")
      .attr('marker-end', function(d) {
        if (d && d.new_weight > 0) {
          if(id == d.id && group == d.gtype) return "url(#" + d.gtype+"_"+d.type+"_"+d.id + "_selected)";
          else return "url(#" + d.gtype+"_"+d.type+"_"+d.id + ")";
        }
      })
      .style("stroke", function (d) {
        if (d)
        if(id == d.id && group == d.gtype) { if (d.type == "in") return selcolor[0]; else return selcolor[1]; }
        else if(group != d.gtype) { if (d.type == "in") return norcolor[0]; else return norcolor[1]; }
        else { if (d.type == "in") return hidcolor[0]; else return hidcolor[1]; }
      })
      .style("opacity", function (d) {
        if (d)
        if(id != d.id && group == d.gtype) return 0.4;
      });
  } else {
    svg[idx].selectAll(".link")
      .attr('marker-end', function(d) {
        if (d)
        if(id == d.id && group == d.gtype) return "url(#" + d.gtype+"_"+d.type+"_"+d.id + "_selected)";
        else return "url(#" + d.gtype+"_"+d.type+"_"+d.id + ")";
      })
      .style("stroke", function (d) {
        if (d)
        if(id == d.id && group == d.gtype) { if (d.type == "in") return selcolor[0]; else return selcolor[1]; }
        else if(group != d.gtype) { if (d.type == "in") return norcolor[0]; else return norcolor[1]; }
        else { if (d.type == "in") return hidcolor[0]; else return hidcolor[1]; }
      })
      .style("opacity", function (d) {
        if (d)
        if(id != d.id && group == d.gtype) return 0.4;
      });
  }
}

function highlight_off(idx, compare_ref) {
  if (compare_ref) {
    svg[idx].selectAll(".new-link")
      .attr('marker-end', function(d) { if (d.new_weight > 0) return "url(#" + d.gtype+"_"+d.type+"_"+d.id + ")"; })
      .style("stroke", function (d) { if (d.type == "in") return norcolor[0]; else return norcolor[1]; })
      .style("opacity", function (d) { if (d) return 1; } );
  } else {
    svg[idx].selectAll(".link")
      .attr('marker-end', function(d) { if (d) return "url(#" + d.gtype+"_"+d.type+"_"+d.id + ")"; })
      .style("stroke", function (d) { if (d) if (d.type == "in") return norcolor[0]; else return norcolor[1]; })
      .style("opacity", function (d) { if (d) return 1; } );
  }

  // un-highlight rectangles
  svg[idx].selectAll("rect").each(function() {
    if (d3.select(this).attr("class") == "bar") {
        d3.select(this).style("opacity", 1);
    }
  });

  // un-highlight bar text
  svg[idx].selectAll("text").each(function() {
    if (d3.select(this).classed("hl-bar-text")) {
        d3.select(this).style("opacity", 1);
    }
  });

  // un-highlight text
  svg[idx].selectAll("text").each(function() {
    if (d3.select(this).classed("hl-text")) {
        d3.select(this).style("opacity", 1);
    }
  });

  // un-highlight circles
  if (compare_ref) {
    svg[idx].selectAll("circle").each(function() {
      if (d3.select(this).attr("class") == "hl-circle-new") {
          d3.select(this).style("opacity", 1);
      }
    });
  } else {
    svg[idx].selectAll("circle").each(function() {
      if (d3.select(this).attr("class") == "hl-circle") {
          d3.select(this).style("opacity", 1);
      }
    });
  }
}

function linkArc(idx, d, bloom) {
  var source = node_out[idx]._groups[0][d.source],
      target = node_out[idx]._groups[0][d.target];
  var sx, sy, tx, ty;
  if (bloom) {
    sx = parseInt(source.getAttribute("xpos")), sy = parseInt(source.getAttribute("ypos")),
    tx = parseInt(target.getAttribute("xpos")), ty = parseInt(target.getAttribute("ypos"));
  } else {
    sx = parseInt(source.getAttribute("cx")), sy = parseInt(source.getAttribute("cy")),
    tx = parseInt(target.getAttribute("cx")), ty = parseInt(target.getAttribute("cy"));
  }
  var dx = tx-sx,
      dy = ty-sy,
      dr = Math.sqrt(dx * dx + dy * dy)*2;
  return "M" + sx + "," + sy + "A" + dr + "," + dr + " 0 0,1 " + tx + "," + ty;
}

function nodeRadius(size) {
  return (Math.sqrt((node_max_area/Math.PI)*size)*window_scaling_factor);
}

function split_flower(idx, shift) {

  // Move text wrt shift
  text_out[idx].transition()
    .each(function() {
        d3.select(this).transition()
            .duration(2000)
            .attr("transform", "translate(" + shift + ", 0)");
    });

  // Move nodes wrt shift
  node_out[idx].transition()
    .each(function() {
        d3.select(this).transition()
            .duration(2000)
            .attr("transform", "translate(" + shift + ", 0)");
    });

  link[idx].transition()
    .each(function() {
        if (d3.select(this).attr("class") == "link in")
            { var move = -shift }
        else
            { var move = shift }
        d3.select(this).transition()
            .duration(2000)
            .attr("transform", "translate(" + move + ", 0)");
    });
}

function toggle_split(idx, selected) {
    // var split_distance = width/4,
    //     id = d3.select(selected).attr("id");
    //
    // if (id != 0) { return; }
    //
    // // If click the ego, then split flower
    // if (flower_split[idx]) {
    //     split_flower(idx, 0);
    //     flower_split[idx] = false;
    //     split_button[idx].select("text")
    //         .text("Split Flower")
    // }
    // else {
    //     split_flower(idx, split_distance);
    //     flower_split[idx] = true;
    //     split_button[idx].select("text")
    //         .text("Combine Flower")
    // }
}

function arrow_width_calc(weight) {
    if (weight == 0) { return 0; }
    else { return 1+8*weight; }
    }

function arrow_size_calc(weight) {
    if (weight == 0) { return 0; }
    else { return 15; }
    }


function genNodeInfoTitleStr(info_dict) {
    // Make node paper title string
    var title_str = "<i>" + info_dict["link_title"] + "</i>";
    title_str += ": " + info_dict["link_year"];

    return title_str;
}


function genNodeInfoPaperStr(info_dict) {
    // Make node paper information string
    var info_str = "";

    // Author display
    if (info_dict['type'] != 'AUTH') {
        info_str += "Authors: " + info_dict["link_auth"].join(', ');
        info_str += "<br>";
    }

    // Venue display
    if (info_dict['type'] != 'CONF' && info_dict['type'] != 'JOUR') {
        // Join journal and conferences
        var venues = info_dict["link_conf"].concat(info_dict["link_jour"]);
        venues = venues.filter(n => n);

        if (venues.length > 0) {
            info_str += "Venues: " + venues.join(', ');
        } else {
            info_str += "Venues: Not Specified";
        }
        info_str += "<br>";
    }

    return info_str;
}

function genNodeInfoListElement(info_dict) {
    // Make the list elements
    var title_str = genNodeInfoTitleStr(info_dict);
    var paper_str = genNodeInfoPaperStr(info_dict);

    var info_str = "<li>";

    info_str += title_str;

    // Add button for collapsed information
    var id = info_dict["link_title"].replace(/\s+/g, '-') + "-info";
    info_str += "<button type=\"button\" ";
    //info_str += "class=\"btn\" "; // ADD BUTTON CLASS HERE
    info_str += "data-toggle=\"collapse\" ";
    info_str += "data-target=\"#" + id + "\" ";
    info_str += ">More Information</button>";

    info_str += "<div id=\"" + id + "\" class=\"collapse\">";
    info_str += paper_str;
    info_str += "</div>";

    info_str += "</li>";

    return info_str;
}


// Colours for the node information table
var even_cit = '#6faed1cc';
var even_ref = '#e48268cc';
var even_ego = '#e0e0e0';
var odd_cit  = '#6faed180';
var odd_ref  = '#e4826899';
var odd_ego  = '#e0e0e099';

// Counter for paging
var page_counter = 0;
var max_page_num = 0;
var node_info_name = '';
var node_info_type = '';
var display_name   = '';
var flower_name    = '';


function formatNodeInfoHeader(data) {
  var title = "<h3 style='display: inline;margin-right: 10px;'>"+display_name+"</h3>";

  return "<div id='node_info_header' class='node_info_header'>"+title+"</div>";
}


function formatNodeInfoLower(data) {
  page_counter = 1;
  max_page_num = data["max_page"];

  var next_button = "<button id='next_node_page' onclick='nextPage()'>Next</button>";
  var prev_button = "<button id='prev_node_page' onclick='prevPage()'>Prev</button>";
  var page_indicate = "<p id='page_indicate' style='display: inline; margin: 5px;'>" + page_counter + "/" + max_page_num + "</p>";

  return "<div id='node_info_lower' class='node_info_lower'>"+prev_button+page_indicate+next_button+"</div>";
}


function formatNodeInfoTable(data) {
  var links = data["node_links"];
  var paper_map = data["paper_info"];
  var node_name = data["node_name"];
  var entities = data.entity_names;

  var style_str = "";
  var link_table = "<table>";

  var bg_color_counter = 0;

  var table_str = "";
  for (var i=0; i<links.length; i++) {
      var references = links[i]["reference"];
      var citations  = links[i]["citation"];

      var link_length = Math.max(references.length, citations.length);
      var ego_info = paper_map[links[i]["ego_paper"]];
      var ego_str = formatCitation(ego_info, data.entity_names, node_name);
      var ego_html = function (x) { return "<td width='32%' style='background-color:" + x + "'>" + ego_str + "</td>"; };
      var ego_empty = function (x) { return "<td width='32%' style='background-color:" + x + "'></td>"; };

      for (var j=0; j<link_length; j++) {
          // Set background colour
          if (bg_color_counter % 2 == 0) {
              var ref_color = even_ref;
              var cit_color = even_cit;
              var ego_color = even_ego;
          } else {
              var ref_color = odd_ref;
              var cit_color = odd_cit;
              var ego_color = odd_ego;
          }

          bg_color_counter ++;

          table_str += "<tr>";
          if (j < citations.length) {
              var cit_info = paper_map[citations[j]];
              var cit_str = formatCitation(cit_info, data.entity_names, node_name);
              var cit_html  = function (x) { return "<td width='32%' style='background-color:" + x + "'>" + cit_str + "</td>"; };
              var cit_arrow = function (x) { return "<td width='2%' style='color: rgb(107,172,208); font-size: 30px; background-color:" + x + "'>⟶</td>"; };
          } else {
              //var cit_html = function (x) { return "<td width='32%' style='background-color:" + x + "'></td>"; };
              var cit_html = function (x) { return "<td width='32%' style='cursor: default;'></td>"; };
              var cit_arrow = function (x) { return "<td width='2%' style='cursor: default;'></td>"; };
          }

          if (j < references.length) {
              var ref_info = paper_map[references[j]];
              var ref_str = formatCitation(ref_info, data.entity_names, node_name);
              var ref_html = function (x) { return "<td width='32%' style='background-color:" + x + "'>" + ref_str + "</td>"; };
              var ref_arrow = function (x) { return "<td width='2%' style='color: rgb(228,130,104); font-size: 30px; background-color:" + x + "'>⟶</td>"; };
          } else {
              //var ref_html = function (x) { return "<td width='32%' style='background-color:" + x + "'></td>"; };
              var ref_html = function (x) { return "<td width='32%' style='cursor: default;'></td>"; };
              var ref_arrow = function (x) { return "<td width='2%' style='cursor: default;'></td>"; };
          }

          if (j == 0) {
              table_str += cit_html(cit_color) + cit_arrow(ego_color) + ego_html(ego_color)  + ref_arrow(ego_color) + ref_html(ref_color);
          } else {
              table_str += cit_html(cit_color) + cit_arrow(ego_color) + ego_empty(ego_color) + ref_arrow(ego_color) + ref_html(ref_color);
          }
          table_str += "</tr>";
      }
      table_str += "<tr style='border-bottom: 0px solid white;'><td style='height: 1px; cursor: default;' colspan='5'></td></tr>";
  }
  link_table += "<tr> <th>" + display_name + " has influenced</th> <th style='font-size: 30px'>⟶</th>";
  link_table += "<th>" + flower_name + "</th> <th style='font-size: 30px'>⟶</th> <th> influencing " + display_name + "</th> </tr>";
  link_table += table_str;
  link_table += "</table>";

  return "<div id='node_info_content'>"+link_table+"</div>";
}


function populateNodeInfoContent(data){
  var container_div = document.getElementById("node_info_container");
  var content_div = document.getElementById("node_info_content");
  var header_div = document.getElementById("node_info_header");
  var lower_div = document.getElementById("node_info_lower");

  if (content_div) {
      container_div.removeChild(content_div);
  }
  if (header_div) {
      container_div.removeChild(header_div);
  }
  if (lower_div) {
      container_div.removeChild(lower_div);
  }

  // Make header
  var header_string = formatNodeInfoHeader(data);
  var html_elem = new DOMParser().parseFromString(header_string, 'text/html').body.childNodes;
  container_div.appendChild(html_elem[0]);

  // Make content
  var html_string = formatNodeInfoTable(data);
  var html_elem = new DOMParser().parseFromString(html_string, 'text/html').body.childNodes;
  container_div.appendChild(html_elem[0]);
  $(function () {
    $('[data-toggle="tooltip"]').tooltip()
  })

  // Make lower
  var lower_string = formatNodeInfoLower(data);
  var html_elem = new DOMParser().parseFromString(lower_string, 'text/html').body.childNodes;
  container_div.appendChild(html_elem[0]);
}


// rgb(107, 172, 208); blue
//  rgb(228, 130, 104);oranger

function getData(param){
  node_info_name = param['name'].toLowerCase();
  node_info_type = param['gtype'];
  console.log(node_info_name);
  var data_dict = { // input to the views.py - search()
      "name": node_info_name,
      "node_type": node_info_type,
      "session": session
    };
    var t0 = performance.now();
  $.ajax({
    type: "POST",
    url: "/get_node_info/",
    data: {"data_string": JSON.stringify(data_dict)},
    success: function (result) { // return data if success

      console.log(result);
      display_name = capitalizeString(result['node_type'], result['node_name']);
      flower_name  = result['flower_name'];
      populateNodeInfoContent(result);
      document.getElementById("prev_node_page").disabled=true;
      if (result['max_page']===1){document.getElementById("next_node_page").disabled=true}
      document.getElementById("node_info_modal").style.display = "block";
    },
    error: function (result) {
    }
  });
}


function getNodeName(e){
  var type = e.getAttribute('gtype');
  var id = e.getAttribute('id');
  var res = [];
  $(e.parentElement.parentElement).find('text').each(function(){
    if (this.getAttribute('gtype')==type && this.getAttribute('id')==id){
      res.push(this);
    }
  });
  for (i in res){
    if (res[i].textContent !== ""){return res[i].textContent};
  }
}


function showNodeData(idx, selected){
    var name = getNodeName(selected);
    var data = getData({"name": name, 'gtype': selected.getAttribute('gtype')});
}

function hideNodeData(){
    document.getElementById('node_info_modal').style.display = "none";
}

function nextPage() {
  if (page_counter != max_page_num) {
    var data_dict = { // input to the views.py - search()
        "name": node_info_name,
        "node_type": node_info_type,
        "page": page_counter + 1,
        "session": session
      };
    $.ajax({
      type: "POST",
      url: "/get_next_node_info_page/",
      data: {"data_string": JSON.stringify(data_dict)},
      success: function (result) { // return data if success
        var content_div = document.getElementById("node_info_content");

        // Make content
        var html_string = formatNodeInfoTable(result);
        var html_elem = new DOMParser().parseFromString(html_string, 'text/html').body.childNodes;
        content_div.replaceWith(html_elem[0]);

        document.getElementById("node_info_modal").style.display = "block";

        // Set the page number
        page_counter = Math.min(page_counter + 1, max_page_num);
        document.getElementById("page_indicate").innerHTML = page_counter + "/" + max_page_num;
        if (page_counter === max_page_num){document.getElementById("next_node_page").disabled=true}
        document.getElementById("prev_node_page").disabled=false;
      },
      error: function (result) {
      }
    });
  }
}

function prevPage() {
  if (page_counter != 1) {
    var data_dict = { // input to the views.py - search()
        "name": node_info_name,
        "node_type": node_info_type,
        "page": page_counter - 1,
        "session": session
      };
    $.ajax({
      type: "POST",
      url: "/get_next_node_info_page/",
      data: {"data_string": JSON.stringify(data_dict)},
      success: function (result) { // return data if success
        var content_div = document.getElementById("node_info_content");

        // Make content
        var html_string = formatNodeInfoTable(result);
        var html_elem = new DOMParser().parseFromString(html_string, 'text/html').body.childNodes;
        content_div.replaceWith(html_elem[0]);

        document.getElementById("node_info_modal").style.display = "block";

        // Set the page number
        page_counter = Math.max(page_counter - 1, 1);
        document.getElementById("page_indicate").innerHTML = page_counter + "/" + max_page_num;
        if (page_counter === 1){document.getElementById("prev_node_page").disabled=true}
        document.getElementById("next_node_page").disabled=false;
      },
      error: function (result) {
      }
    });
  }
}

function capitalizeString(entity_type, string) {
    var words = string.split(' ');
    var res = [];
    // console.log(entity_type, string, words.length)
    if ((entity_type == "conf" && words.length == 1 && string.length < 8) // for conf names
      || (entity_type == "inst" && words.length == 1 && string.length < 5)) // for inst names
      return string.toUpperCase();

    var stopwords = ["and", "or", "of", "the", "at", "on", "in", "for"],
        capwords = ["ieee", "acm", "siam", "eth", "iacr", "ieice"];
    var spacialcase = {"arxiv": "arXiv:"}
    for (i = 0; i < words.length; i++) {
        var fwords = words[i];
        if (capwords.includes(fwords)) {
          fwords = words[i].toUpperCase();
        } else if (spacialcase[fwords] != undefined) {
          fwords = spacialcase[words[i]];
        } else if (!stopwords.includes(fwords)) {
          fwords = words[i].charAt(0).toUpperCase() + words[i].slice(1);
        }
        res.push(fwords);
    }

    return res.join(' ');
}

function barText(e_id, string) {
    // console.log("barText", string)
    e_types = ["author", "conf", "inst", "fos"];
    var str = capitalizeString(e_types[e_id], string.slice(0, 24));
    if (string.length > 24) {
        return str.slice(0, 20)+"...";
    }
    else {
        return str;
    }
}

// ---------- Ordering and Sorting ----------
function reorder(num, order, data) {
  var sortable_data = data.nodes
    .slice(1)
    .filter(function(d) { return d.bloom_order <= num; } );

  // Pick the sort ordering
  if (order == "blue") {
    var sort_func = blue_order;
  }
  else if (order == "red") {
    var sort_func = red_order;
  }
  else if (order == "total") {
    var sort_func = total_order;
  }
  else {
    var sort_func = ratio_order;
  }

  var sort_index = {0:0};

  for (var i in sortable_data.sort(sort_func)) {
    sort_index[sortable_data[i].id] = parseInt(i) + 1;
  }

  return sort_index;
}

function blue_order(a, b) {
  return - (a.inf_out - b.inf_out);
}

function red_order(a, b) {
  return - (a.inf_in - b.inf_in);
}

var SORT_TOL = 1e-9;

function total_order(a, b) {
  var a_val = a.size + SORT_TOL * a.dif;
  var b_val = b.size + SORT_TOL * b.dif;
  return - (a_val - b_val);
}

function ratio_order(a, b) {
  var a_val = a.ratio + SORT_TOL * a.dif;
  var b_val = b.ratio + SORT_TOL * b.dif;
  return - (a_val - b_val);
}

function node_order(ordering, a, b) {
  var a_val = ordering[a.id];
  var b_val = ordering[b.id];

  return - (a_val - b_val);
}

function link_order(ordering, a, b) {
  var a_val = ordering[a.id];
  var b_val = ordering[b.id];
  if (a.class == "link_out") a_val += 0.5;
  if (b.class == "link_out") b_val += 0.5;

  return a_val - b_val;
}

// ---------- Transform and Positions ----------
function linspace(start, end, num) {
  if (num > 1) {
    var step = (end - start) / (num - 1);
  }
  else {
    var step = 0;
  }
  var lin = [];

  for (var i = 0; i < num; i++) {
    lin.push(start + i * step);
  }

  return lin;
}

var RADIUS = 1.2;

function gen_pos(num) {
  if (num > 25) {
    var angles = linspace(Math.PI * (1 + (num - 25) / num / 2), - Math.PI * (num - 25) / num / 2, num);
  }
  else if (num < 10) {
    var angles = linspace(Math.PI * (0.5 + num / 20), Math.PI * (0.5 - num / 20), num);
  }
  else {
    var angles = linspace(Math.PI, 0, num);
  }

  var x_pos = {0: 0};
  var y_pos = {0: 0};

  for (var i in angles) {
    var angle = angles[i];
    x_pos[parseInt(i)+1] = RADIUS * Math.cos(angle);
    y_pos[parseInt(i)+1] = RADIUS * Math.sin(angle);
  }

  return [x_pos, y_pos];
}

function text_order_xpos(d, xpos, ordering) {
  shift = 0;
  circ_dif = 5;
  xval = xpos[ordering[d.id]];

  if (xval < -.3) shift -= nodeRadius(d.size) + circ_dif;
  if (xval > .3) shift += nodeRadius(d.size) + circ_dif;

  return center[0] + magf*xval + shift;
}

function text_order_ypos(d, xpos, ypos, num, ordering) {
  shift = 0;
  scale = num/20;
  xval = xpos[ordering[d.id]];
  yval = ypos[ordering[d.id]];

  for(i = 6; i >= 0; i--) {
      xpos_p = i/10+0.05;
      if (d.id > 0 && -xpos_p < xval && xval < xpos_p) shift -= (7-i)*scale;
  }

  // Title
  if (d.id == 0) {
      shift += 50;
  }

  return center[1] - magf*yval + shift;
}

function text_order_anchor(d, xpos, ordering) {
  xval = xpos[ordering[d.id]];

  if (xval < -0.1) return "end";
  else if (xval > 0.1) return "start";
  else return "middle";
}

// ---------- Reorder Move ----------
var GTYPE_MAP = {0: "author", 1: "conf", 2: "inst", 3: "fos"};

function linkOrderUpdate(d, ordering, xpos, ypos) {
  var sp_id = ordering[d.source];
  var tp_id = ordering[d.target];

  var sx_pos = center[0] + magf * xpos[sp_id];
  var sy_pos = center[1] - magf * ypos[sp_id];
  var tx_pos = center[0] + magf * xpos[tp_id];
  var ty_pos = center[1] - magf * ypos[tp_id];
  return arcUpdate(sx_pos, sy_pos, tx_pos, ty_pos);
}

function arcUpdate(sx, sy, tx, ty) {
  var dx = tx-sx,
      dy = ty-sy,
      dr = Math.sqrt(dx * dx + dy * dy)*2;
  return "M" + sx + "," + sy + "A" + dr + "," + dr + " 0 0,1 " + tx + "," + ty;
}

// ---------- Disable/Enable Shapes ----------

var PATH_LINK = ["link in", "link out", "new-link in", "new-link out"];

function findLinks(obj) {
  return PATH_LINK.includes(d3.select(obj).attr("class"));
}

function disableBloomNumPaths(num) {
  d3.selectAll("path")
    .filter(function() { return findLinks(this); })
    .filter(function(d) {return d.bloom_order <= num;} )
    .style("visibility", "visible");

  d3.selectAll("path")
    .filter(function() { return findLinks(this); })
    .filter(function(d) {return d.bloom_order <= num;} )
    .transition()
    .duration(2000)
    .style("opacity", 1.0);

  d3.selectAll("path")
    .filter(function() { return findLinks(this); })
    .filter(function(d) {return d.bloom_order > num;} )
    .transition()
    .duration(2000)
    .style("opacity", 0.0)
    .transition()
    .delay(2000)
    .style("visibility", "hidden");
}

function disableBloomNumText(num) {
  d3.selectAll("text")
    .filter(function(d) { if (d != undefined) return d.bloom_order <= num; } )
    .style("visibility", "visible");

  d3.selectAll("text")
    .filter(function(d) { if (d != undefined) return d.bloom_order <= num; } )
    .transition()
    .duration(2000)
    .style("opacity", 1.0);

  d3.selectAll("text")
    .filter(function(d) { if (d != undefined) return d.bloom_order > num; } )
    .transition()
    .duration(2000)
    .style("opacity", 0.0)
    .transition()
    .delay(2000)
    .style("visibility", "hidden");
}

function barColour(d) {
  if (d.type == "in") return norcolor[0];
  else return norcolor[1];
}

function disableBloomNumBars(num, duration) {
  d3.selectAll("rect")
    .filter(function(d) { if (d != undefined) return d.bloom_order <= num; } )
    .interrupt()
    .transition()
    .duration(duration)
    .style("fill", barColour);

  d3.selectAll("rect")
    .filter(function(d) { if (d != undefined) return d.bloom_order > num; } )
    .interrupt()
    .transition()
    .duration(duration)
    .style("fill", "#ddd");
}

function reorder_flower_grow(idx, num, order, duration) {
  var ordering = reorder(num, order, data_arr[idx]);
  var [xpos, ypos] = gen_pos(num);

  // -- Reorder the layering --
  d3.selectAll("circle")
    .filter(function(d) { return d.gtype == GTYPE_MAP[idx]; } )
    .sort(function(a, b) { return node_order(ordering, a, b); } );

  d3.selectAll("path")
    .filter(function() { return findLinks(this); })
    .filter(function(d) { return d.gtype == GTYPE_MAP[idx]; } )
    .sort(function(a, b) { return node_order(ordering, a, b); } );
  // -- Reorder the layering --

  // -- Re-enable --
  d3.selectAll("circle")
    .filter(function(d) { return d.gtype == GTYPE_MAP[idx]; } )
    .filter(function(d) {return d.bloom_order <= num;} )
    .style("visibility", "visible");

  d3.selectAll("path")
    .filter(function() { return findLinks(this); })
    .filter(function(d) { return d.gtype == GTYPE_MAP[idx]; } )
    .filter(function(d) {return d.bloom_order <= num;} )
    .style("visibility", "visible");

  d3.selectAll("text")
    .filter(function(d) { if (d != undefined) return d.bloom_order <= num; } )
    .filter(function(d) { return d.gtype == GTYPE_MAP[idx]; } )
    .style("visibility", "visible");
  // -- Re-enable --

  // -- Move Then Enable --
  d3.selectAll("circle")
    .filter(function(d) { return d.bloom_order <= num; })
    .filter(function(d) { return d.gtype == GTYPE_MAP[idx]; } )
    .interrupt()
    .transition()
    .duration(duration)
    .attr("cx", function(d) { return center[0]+magf*xpos[ordering[d.id]]; })
    .attr("cy", function(d) { return center[1]-magf*ypos[ordering[d.id]]; })
    .attr("xpos", function(d) { return center[0]+magf*xpos[ordering[d.id]]; })
    .attr("ypos", function(d) { return center[1]-magf*ypos[ordering[d.id]]; })
    .transition()
    .duration(duration)
    .style("opacity", 1.0);

  d3.selectAll("text")
    .filter(function(d) { if (d != undefined) return d.bloom_order <= num; } )
    .filter(function(d) { return d.gtype == GTYPE_MAP[idx]; } )
    .interrupt()
    .transition()
    .duration(duration)
    .attr("x", function(d) { return text_order_xpos(d, xpos, ordering); })
    .attr("y", function(d) { return text_order_ypos(d, xpos, ypos, num, ordering); })
    .attr("text-anchor", function(d) { return text_order_anchor(d, xpos, ordering); })
    .transition()
    .duration(duration)
    .style("opacity", 1.0);

  d3.selectAll("path")
    .filter(function() { return findLinks(this); })
    .filter(function(d) { return d.bloom_order <= num; })
    .filter(function(d) { return d.gtype == GTYPE_MAP[idx]; } )
    .interrupt()
    .transition()
    .duration(duration)
    .attr("d", function(d) { return linkOrderUpdate(d, ordering, xpos, ypos); })
    .transition()
    .duration(duration)
    .style("opacity", 1.0);
  // -- Move Then Enable --
}

var LEAF_FALL = 350;

function reorder_flower_shrink(idx, num, order, duration) {
  var ordering = reorder(num, order, data_arr[idx]);
  var [xpos, ypos] = gen_pos(num);

  // -- Reorder the layering --
  d3.selectAll("circle")
    .filter(function(d) { return d.gtype == GTYPE_MAP[idx]; } )
    .sort(function(a, b) { return node_order(ordering, a, b); } );

  d3.selectAll("path")
    .filter(function() { return findLinks(this); })
    .filter(function(d) { return d.gtype == GTYPE_MAP[idx]; } )
    .sort(function(a, b) { return node_order(ordering, a, b); } );
  // -- Reorder the layering --

  // -- Wait then Move --
  d3.selectAll("circle")
    .filter(function(d) { return d.bloom_order <= num; })
    .filter(function(d) { return d.gtype == GTYPE_MAP[idx]; } )
    .interrupt()
    .transition()
    .delay(duration)
    .duration(duration)
    .attr("cx", function(d) { return center[0]+magf*xpos[ordering[d.id]]; })
    .attr("cy", function(d) { return center[1]-magf*ypos[ordering[d.id]]; })
    .attr("xpos", function(d) { return center[0]+magf*xpos[ordering[d.id]]; })
    .attr("ypos", function(d) { return center[1]-magf*ypos[ordering[d.id]]; })
    .style("opacity", 1.0);

  d3.selectAll("text")
    .filter(function(d) { if (d != undefined) return d.bloom_order <= num; } )
    .filter(function(d) { return d.gtype == GTYPE_MAP[idx]; } )
    .interrupt()
    .transition()
    .delay(duration)
    .duration(duration)
    .attr("x", function(d) { return text_order_xpos(d, xpos, ordering); })
    .attr("y", function(d) { return text_order_ypos(d, xpos, ypos, num, ordering); })
    .attr("text-anchor", function(d) { return text_order_anchor(d, xpos, ordering); })
    .style("opacity", 1.0);

  d3.selectAll("path")
    .filter(function() { return findLinks(this); })
    .filter(function(d) { return d.bloom_order <= num; })
    .filter(function(d) { return d.gtype == GTYPE_MAP[idx]; } )
    .interrupt()
    .transition()
    .delay(duration)
    .duration(duration)
    .attr("d", function(d) { return linkOrderUpdate(d, ordering, xpos, ypos); })
    .style("opacity", 1.0);
  // -- Wait then Move --

  // -- Move and Disable
  d3.selectAll("circle")
    .filter(function(d) { return d.bloom_order > num; })
    .filter(function(d) { return d.gtype == GTYPE_MAP[idx]; } )
    .interrupt()
    .transition()
    .duration(duration*2)
    //.attr("cx", center[0])
    .attr("cy", center[1] + LEAF_FALL)
    //.attr("xpos", center[0])
    .attr("ypos", center[1] + LEAF_FALL)
    .style("opacity", 0.0)
    .transition()
    .style("visibility", "hidden");

  d3.selectAll("text")
    .filter(function(d) { if (d != undefined) return d.bloom_order > num; } )
    .filter(function(d) { return d.gtype == GTYPE_MAP[idx]; } )
    .interrupt()
    .transition()
    .duration(duration*2)
    //.attr("x", center[0])
    .attr("y", center[1] + LEAF_FALL)
    .style("opacity", 0.0)
    .transition()
    .style("visibility", "hidden");

  d3.selectAll("path")
    .filter(function() { return findLinks(this); })
    .filter(function(d) { return d.bloom_order > num; })
    .filter(function(d) { return d.gtype == GTYPE_MAP[idx]; } )
    .interrupt()
    .transition()
    .duration(duration*2)
    .style("opacity", 0.0)
    .transition()
    .style("visibility", "hidden");
  // -- Move and Disable
}

function reorder_all_flowers_grow(num, order, duration) {
  disableBloomNumBars(num, 2*duration);
  for (var idx in data_arr) {
    reorder_flower_grow(idx, num, order, duration);
  }
}

function reorder_all_flowers_shrink(num, order, duration) {
  disableBloomNumBars(num, 2*duration);
  for (var idx in data_arr) {
    reorder_flower_shrink(idx, num, order, duration);
  }
}