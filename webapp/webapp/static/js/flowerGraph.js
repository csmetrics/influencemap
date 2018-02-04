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

var center;
var link = [], flower_state = [], bar = [],
    numnodes = [], svg = [], simulation = [],
    node_in = [], node_out = [],
    text_in = [], text_out = [];

function drawFlower(svg_id, data, idx) {
    var nodes = data["nodes"];
    var links = data["links"];
    var bars = data["bars"];

    h_margin = 100;
    v_margin = 200;
    yheight = 100;
    flower_margin = 50;

    svg[idx] = d3.select(svg_id),
    width = svg[idx].attr("width"),
    height = 600,
    numnodes[idx] = nodes.length,
    center = [width/2, height/2 + flower_margin];
    flower_state[idx] = false;

    // bar location
    bar_width_ratio = 0.9,
    bar_left = h_margin+width*(1-bar_width_ratio),
    bar_right = width*bar_width_ratio-h_margin;

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
        .attr("x", function(d) { if (d.type == "in") return x(d.name)+x.bandwidth()/2; else return x(d.name); })
        .attr("width", x.bandwidth()/2)
        .attr("y", function(d) { return y(d.weight)-v_margin; })
        .attr("height", function(d) { return yheight - y(d.weight); })
        .attr("transform", "translate(0," + height + ")")
        .style("fill", function(d) { if (d.type == "in") return norcolor[0]; else return norcolor[1]; });

    // bar chart x axis
    svg[idx].append("g")
        .attr("transform", "translate(0," + (height+yheight-v_margin) + ")")
        .call(d3.axisBottom(x))
        .selectAll("text")
          .style("text-anchor", "end")
          .attr("dx", "-.8em")
          .attr("dy", "-.5em")
          .attr("transform", "rotate(-90)");;

    // bar chart y axis
    svg[idx].append("g")
        .attr("transform", "translate(" + bar_left + "," + (height-v_margin) + ")")
        .call(d3.axisLeft(y).ticks(5));

    // flower graph edge arrow
    svg[idx].append("defs").selectAll("marker")
        .data(links)
      .enter().append("marker")
        .attr("id", function(d) { return d.gtype+"_"+d.type+"_"+d.id; })
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", function (d) { return 10+10*d.padding; })
        .attr("refY", 0)
        .attr("markerWidth", 15)
        .attr("markerHeight", 15)
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
        .attr("refX", function (d) { return 10+10*d.padding; })
        .attr("refY", 0)
        .attr("markerWidth", 15)
        .attr("markerHeight", 15)
        .attr("markerUnits", "userSpaceOnUse")
        .attr("orient", "auto")
      .append("path")
        .attr("d", "M0,-5L10,0L0,5")
        .style("fill", function (d) { if (d.type == "in") return selcolor[0]; else return selcolor[1]; });

    // flower graph edges
    link[idx] = svg[idx].append("g").selectAll("path")
        .data(links)
      .enter().append("path")
        .attr("id", function(d) { return d.id; })
        .attr("gtype", function(d) { return d.gtype; })
        .attr("class", function(d) { return "link " + d.type; })
        .attr('marker-end', function(d) { return "url(#" + d.gtype+"_"+d.type+"_"+d.id + ")"; })
        .attr("type", function(d) {d.type})
        .style("stroke-width", function (d) { return 1+8*d.weight; })
        .style("stroke", function (d) { if (d.type == "in") return norcolor[0]; else return norcolor[1]; })
        .on("mouseover", function() { highlight_on(idx, this); })
        .on("mouseout", function() { highlight_off(idx); });

    // flower graph nodes
    node_in[idx] = svg[idx].append("g").selectAll("circle")
        .data(nodes)
      .enter().append("circle")
        .attr("id", function(d) { return d.id; })
        .attr("gtype", function(d) { return d.gtype; })
        .attr("r", function(d) { return 5+10*d.size; })
        .style("fill", function (d, i) {if (d.id == 0) return "#ccc"; else return colors(d.weight);})
        .style("stroke-width", function(d) { if (d.coauthor == 'False') return 3; else return 2; })
        .style("stroke", function(d) { if (d.coauthor == 'False') return "grey"; else return "green"; })
        .on("click", function() { toggle_flower(idx, this); })
        .on("mouseover", function() { highlight_on(idx, this); })
        .on("mouseout", function() { highlight_off(idx); });

    // flower graph nodes
    node_out[idx] = svg[idx].append("g").selectAll("circle")
        .data(nodes)
      .enter().append("circle")
        .attr("id", function(d) { return d.id; })
        .attr("gtype", function(d) { return d.gtype; })
        .attr("r", function(d) { return 5+10*d.size; })
        .style("fill", function (d, i) {if (d.id == 0) return "#ccc"; else return colors(d.weight);})
        .style("stroke-width", function(d) { if (d.coauthor == 'False') return 3; else return 2; })
        .style("stroke", function(d) { if (d.coauthor == 'False') return "grey"; else return "green"; })
        .on("click", function() { toggle_flower(idx, this); })
        .on("mouseover", function() { highlight_on(idx, this); })
        .on("mouseout", function() { highlight_off(idx); });

    // flower graph node text
    text_in[idx] = svg[idx].append("g").selectAll("text")
        .data(nodes)
      .enter().append("text")
        .attr("id", function(d) { return d.id; })
        .attr("gtype", function(d) { return d.gtype; })
        .attr("x", 8)
        .attr("y", ".31em")
        .text(function(d) { return d.name; });

    // flower graph node text
    text_out[idx] = svg[idx].append("g").selectAll("text")
        .data(nodes)
      .enter().append("text")
        .attr("id", function(d) { return d.id; })
        .attr("gtype", function(d) { return d.gtype; })
        .attr("x", 8)
        .attr("y", ".31em")
        .text(function(d) { return d.name; });

    // flower graph chart layout
    simulation[idx] = d3.forceSimulation(nodes)
        .force("charge", d3.forceManyBody().strength(-80))
        .force("link", d3.forceLink(links).id(function (d) {return d.id;}).distance(300).strength(1).iterations(0))
        .force("x", d3.forceX())
        .force("y", d3.forceY())
        .on("tick", function() { ticked(idx); });
}

function highlight_on(idx, selected) {
  id = d3.select(selected).attr("id");
  group = d3.select(selected).attr("gtype");
  console.log("selected", id, group);
  if (id == 0) return;
  svg[idx].selectAll("rect")
    .style("opacity", function (d) { if(id != d.id && d.id != 0 && group == d.gtype) return 0.4; else return 1; });
  svg[idx].selectAll("text")
    .style("opacity", function (d) { if(id != d.id && d.id != 0 && group == d.gtype) return 0.4; else return 1; });
  svg[idx].selectAll("circle")
    .style("opacity", function (d) { if(id != d.id && d.id != 0 && group == d.gtype) return 0.4; else return 1; });
  svg[idx].selectAll("path")
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

function highlight_off(idx) {
  svg[idx].selectAll("path")
    .attr('marker-end', function(d) { if (d) return "url(#" + d.gtype+"_"+d.type+"_"+d.id + ")"; })
    .style("stroke", function (d) { if (d) if (d.type == "in") return norcolor[0]; else return norcolor[1]; })
    .style("opacity", function (d) { if (d) return 1; } );
  svg[idx].selectAll("circle").style("opacity", function (d) { return 1; });
  svg[idx].selectAll("text").style("opacity", function (d) { return 1; });
  svg[idx].selectAll("rect").style("opacity", function (d) { return 1; });
}

function ticked(idx) {
  link[idx].attr("d", linkArc);
  node_in[idx].attr("cx", transform_x);
  node_in[idx].attr("cy", transform_y);
  node_out[idx].attr("cx", transform_x);
  node_out[idx].attr("cy", transform_y);
  text_in[idx].attr("x", transform_text_x);
  text_in[idx].attr("y", transform_text_y);
  text_out[idx].attr("x", transform_text_x);
  text_out[idx].attr("y", transform_text_y);
  text_in[idx].attr("text-anchor", locate_text);
  text_out[idx].attr("text-anchor", locate_text);
}

function linkArc(d) {
  var dx = d.target.x - d.source.x,
      dy = d.target.y - d.source.y,
      dr = Math.sqrt(dx * dx + dy * dy);
  return "M" + d.source.x + "," + d.source.y + "A" + dr + "," + dr + " 0 0,1 " + d.target.x + "," + d.target.y;
}

function transform_x(d) {
  magf = 250;
  d.fx = center[0]+magf*d.xpos;
  return d.x
}

function transform_y(d) {
  magf = 250;
  d.fy = center[0]+magf*d.ypos;
  return d.y
}

function transform_text_x(d) {
  magf = 250;
  d.fx = center[0]+magf*d.xpos;

  return d.x
}

function transform_text_y(d) {
  magf = 250;
  d.fx = center[0]+magf*d.xpos;
  d.fy = center[1]-magf*d.ypos;

  if (d.id > 0 && -.3 < d.xpos && d.xpos < .3) d.y -= 10;
  if (d.id > 0 && -.2 < d.xpos && d.xpos < .2) d.y -= 10;
  if (d.id > 0 && -.1 < d.xpos && d.xpos < .1) d.y -= 10;
  return d.y
}

function locate_text(d) {
  if (d.xpos < -0.1) return "end";
  else if (d.xpos > 0.1) return "start";
  else return "middle";
}

function split_flower(idx, shift) {

  // Move text wrt shift
  text_in[idx].transition()
    .each(function() {
        d3.select(this).transition()
            .duration(2000)
            .attr("transform", "translate(" + shift + ", 0)");
    });

  // Move text wrt shift
  text_out[idx].transition()
    .each(function() {
        d3.select(this).transition()
            .duration(2000)
            .attr("transform", "translate(" + eval(-shift) + ", 0)");
    });

  // Move nodes wrt shift
  node_in[idx].transition()
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
            .attr("transform", "translate(" + eval(-shift) + ", 0)");
    });

  link[idx].transition()
    .each(function() {
        console.log()
        if (d3.select(this).attr("class") == "link in")
            { var move = shift }
        else
            { var move = -shift }
        d3.select(this).transition()
            .duration(2000)
            .attr("transform", "translate(" + move + ", 0)");
    });
}

function toggle_flower(idx, selected) {
    var split_distance = 450
    id = d3.select(selected).attr("id");

    console.log(id)
    console.log(flower_state[idx])

    if (id != 0) return;

    if (flower_state[idx]) {
        split_flower(idx, 0);
        flower_state[idx] = false;
    }
    else {
        split_flower(idx, split_distance); 
        flower_state[idx] = true;
    }
}
