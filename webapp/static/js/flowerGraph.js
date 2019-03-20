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
var link = [], flower_split = [], bar = [],
    numnodes = [], cnode = [], svg = [],
    bar_axis_x = [], bar_axis_y = [],
    node_out = [], text_out = [];

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

function drawFlower(svg_id, data, idx, w) {
    var compare_ref = referenceCheckbox.checked;

    var nodes = data["nodes"];
    var links = data["links"];
    var bars = data["bars"];

    window_scaling_factor = w/1000

    v_margin = 150-(Math.max(5, nodes.length-15)*3);
    yheight = 120-Math.max(20, nodes.length-15);

    svg[idx] = d3.select(svg_id),
    width = w, magf = Math.min(250, width/5),
    height = 600,
    numnodes[idx] = nodes.length,
    center = [width*0.45, height*0.6];
    flower_split[idx] = false;

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
        .attr("x", function(d) { if (d.type == "out") return x(d.name)+x.bandwidth()/2; else return x(d.name); })
        .attr("y", function(d) { return y(d.weight)-v_margin; })
        .attr("width", x.bandwidth()/2)
        .attr("height", function(d) { return yheight - y(d.weight); })
        .attr("transform", "translate(0," + height + ")")
        .style("opacity", 1)
        .style("fill", function(d) { if (d.type == "in") return norcolor[0]; else return norcolor[1]; });

    // bar chart x axis
    bar_axis_x[idx] = svg[idx].append("g")
        .attr("transform", "translate(0," + (height+yheight-v_margin) + ")")
        .call(d3.axisBottom(x))
        .selectAll("text")
          .text(barText)
          .attr("id", function(d, i) { return i+1; })
          .attr("class", "hl-text node-text")
          .style("text-anchor", "end")
          .style("fill", function(d) {
            for (var i in nodes) {
                if (nodes[i]['name'] == d) {
                    if (nodes[i]['coauthor'] == 'True') {
                        return "gray";
                    }
                    else {
                        return "black";
                    }
                }
            };
            return "black"; } )
          .attr("dx", "-.8em")
          .attr("dy", function() {return - x.bandwidth()/15; } )//"-3px")
          .attr("transform", "rotate(-90)");

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
        .attr("refX", function (d) { return 10+200*d.padding/Math.max(15, numnodes[idx]); })
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
        .attr("refX", function (d) { return 10+200*d.padding/Math.max(15, numnodes[idx]); })
        .attr("refY", function (d) { return -d.padding; })
        .attr("markerWidth", function (d) { return window_scaling_factor*arrow_size_calc(d.weight); })
        .attr("markerHeight", function (d) { return window_scaling_factor*arrow_size_calc(d.weight); })
        .attr("markerUnits", "userSpaceOnUse")
        .attr("orient", "auto")
      .append("path")
        .attr("d", "M0,-5L10,0L0,5")
        .style("fill", function (d) { if (d.type == "in") return selcolor[0]; else return selcolor[1]; });

    link_g = svg[idx].append("g");
    node_g = svg[idx].append("g");
    new_link_g = svg[idx].append("g");
    new_node_g = svg[idx].append("g");
    text_g = svg[idx].append("g");

    // flower graph nodes
    original_nodes = node_out[idx] = node_g.selectAll("circle .hl-circle")
        .data(nodes)
      .enter().append("circle")
        .attr("id", function(d) { return d.id; })
        .attr("class", "hl-circle")
        .attr("xpos", function(d) { return transform_x(d); })
        .attr("ypos", function(d) { return transform_y(d); })
        .attr("cx", function(d) { if (d.id > 0) return transform_x(nodes[0]); else return transform_x(d); })
        .attr("cy", function(d) { if (d.id > 0) return transform_y(nodes[0])-magf; else return transform_y(d); })
        .attr("gtype", function(d) { return d.gtype; })
        .attr("r", function(d) { return (8+200*d.size/Math.max(15, numnodes[idx]))*window_scaling_factor; })
        .style("fill", function (d, i) {
          if (d.id == 0) return "#fff";
          else if (compare_ref) return "#ddd"; else return colors(d.weight); s})
        .style("stroke", function (d, i) {
          if (compare_ref) return "ddd";
          else if ((d.coauthor == 'True') && (d.id != 0)) return "green"; else return "";
        })
        .style("stroke-width", 2)
        .style("cursor", "pointer")
        .on("mouseover", function() { highlight_on(idx, this, compare_ref); })
        .on("mouseout", function() { highlight_off(idx, compare_ref); })
        .on("click", function(d) { if (d.id != 0) { showNodeData(idx, this);} })
      .transition()
        .duration(2000)
        .attr("cx", function(d) { return transform_x(d); })
        .attr("cy", function(d) { return transform_y(d); })

    if (compare_ref) {
      // flower graph nodes - new node size
      node_out[idx] = new_node_g.selectAll("circle .hl-circle-new")
          .data(nodes)
        .enter().append("circle")
          .attr("id", function(d) { return d.id; })
          .attr("class", "hl-circle-new")
          .attr("xpos", function(d) { return transform_x(d); })
          .attr("ypos", function(d) { return transform_y(d); })
          .attr("cx", function(d) { if (d.id > 0) return transform_x(nodes[0]); else return transform_x(d); })
          .attr("cy", function(d) { if (d.id > 0) return transform_y(nodes[0])-magf; else return transform_y(d); })
          .attr("gtype", function(d) { return d.gtype; })
          .attr("r", function(d) {
            if (d.new_size >= 0 || d.id == 0) return (8+200*d.new_size/Math.max(15, numnodes[idx]))*window_scaling_factor;
            else return 0})
          .style("fill", function (d, i) {if (d.id == 0) return "#fff"; else return colors(d.new_weight);})
          .style("stroke", function (d, i) { if ((d.coauthor == 'True') && (d.id != 0)) return "green"; else return ""; })
          .style("stroke-width", 2)
          .style("cursor", "pointer")
          .on("mouseover", function() { highlight_on(idx, this, compare_ref); })
          .on("mouseout", function() { highlight_off(idx, compare_ref); })
          .on("click", function(d) { if (d.id != 0) { showNodeData(idx, this);} })
        .transition()
          .duration(2000)
          .attr("cx", function(d) { return transform_x(d); })
          .attr("cy", function(d) { return transform_y(d); })
    }

    // flower graph node text
    text_out[idx] = text_g.selectAll("text")
        .data(nodes)
      .enter().append("text")
        .attr("id", function(d) { return d.id; })
        .attr("class", function(d) { if (d.id == 0) return 'hl-text node-ego-text'; else return 'hl-text node-text'; })
        .attr("gtype", function(d) { return d.gtype; })
        .attr("x", function(d) { if (d.id > 0) return transform_text_x(nodes[0]); else return transform_text_x(d); })
        .attr("y", function(d) { if (d.id > 0) return transform_text_y(nodes[0])-magf; else return transform_text_y(d); })
        .attr("text-anchor", locate_text)
        .text(function(d) { return capitalizeString(d.name); })
        .style("fill", function(d) { if (d.coauthor == 'False') return "black"; else return "gray"; })
      .transition()
        .duration(2000)
        .attr("x", function(d) { return transform_text_x(d); })
        .attr("y", function(d) { return transform_text_y(d); })

    // flower graph edges
    link[idx] = link_g.selectAll("path .link")
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
          else if (d.type == "in") return norcolor[0]; else return norcolor[1];
        })
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
            if (d.new_weight > 0) return window_scaling_factor*arrow_width_calc(d.new_weight); else return 0 })
          .style("stroke", function (d) { if (d.type == "in") return norcolor[0]; else return norcolor[1]; })
        .transition()
          .duration(2000)
          .attr("d", function(d){ return linkArc(idx, d, true); })
    }
}

function highlight_on(idx, selected, compare_ref) {
  id = d3.select(selected).attr("id");
  group = d3.select(selected).attr("gtype");
  if (id == 0) return;

  // highlight rectangles
  svg[idx].selectAll("rect").each(function() {
    if (d3.select(this).attr("class") == "bar") {
        d3.select(this).style("opacity", function (d) { if(id != d.id && d.id != 0 && group == d.gtype) return 0.4; else return 1; });
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

function transform_x(d) {
  return center[0]+magf*d.xpos;
}

function transform_y(d) {
  return center[1]-magf*d.ypos;
}

function transform_text_x(d) {
  shift = 0;
  circ_dif = 5;
  if (d.xpos < -.3) shift -= 8+200*d.size/15 + circ_dif;
  if (d.xpos > .3) shift += 8+200*d.size/15 + circ_dif;
  return transform_x(d) + shift
}

function transform_text_y(d) {
  shift = 0;
  scale = numnodes[0]/20;
  for(i = 6; i > 0; i--) {
      xpos_p = i/10;
      if (d.id > 0 && -xpos_p < d.xpos && d.xpos < xpos_p) shift -= (7-i)*scale;
  }

  // Title
  if (d.id == 0) {
      shift += 50;
  }

  return transform_y(d) + shift
}

function locate_text(d) {
  if (d.xpos < -0.1) return "end";
  else if (d.xpos > 0.1) return "start";
  else return "middle";
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
      display_name = capitalizeString(result['node_name']);
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

function capitalizeString(string) {
    var words = string.split(' ');
    var res = [];

    for (i = 0; i < words.length; i++) {
        var fwords = words[i].charAt(0).toUpperCase() + words[i].slice(1);
        res.push(fwords);
    }

    return res.join(' ');
}

function barText(string) {
    var str = capitalizeString(string.slice(0, 20));
    if (string.length > 20) {
        return str+"...";
    }
    else {
        return str;
    }
}
