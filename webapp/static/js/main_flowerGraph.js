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

function drawFlower(svg_id, data, idx, w) {
    var nodes = data["nodes"];
    var links = data["links"];
    var bars = data["bars"];

    svg[idx] = d3.select(svg_id),
    width = w, magf = 120,
    height = 300,
    numnodes[idx] = nodes.length,
    center = [width*0.45, 200];
    flower_split[idx] = false;

    link_g = svg[idx].append("g");
    node_g = svg[idx].append("g");
    text_g = svg[idx].append("g");

    // flower graph nodes
    node_out[idx] = node_g.selectAll("circle")
        .data(nodes)
      .enter().append("circle")
        .attr("id", function(d) { return d.id; })
        .attr("class", "hl-circle")
        .attr("cx", function(d) { return transform_x(d); })
        .attr("cy", function(d) { return transform_y(d); })
        .attr("gtype", function(d) { return d.gtype; })
        .attr("r", function(d) { return 6+100*d.size/Math.max(15, numnodes[idx]); })
        .style("fill", function (d, i) {if (d.id == 0) return "#fff"; else return colors(d.weight);})
        .style("stroke", function (d, i) { if ((d.coauthor == 'True') && (d.id != 0)) return "green"; else return ""; })
        .style("stroke-width", 2)

    // flower graph node text
    text_out[idx] = text_g.selectAll("text")
        .data(nodes)
      .enter().append("text")
        .attr("id", function(d) { return d.id; })
        .attr("class", function(d) { if (d.id == 0) return 'hl-text node-text'; else return 'hl-text node-text'; })
        .attr("gtype", function(d) { return d.gtype; })
        .attr("x", function(d) { return transform_text_x(d); })
        .attr("y", function(d) { return transform_text_y(d); })
        .attr("text-anchor", locate_text)
        .text(function(d) { return d.name; })
        .style("fill", function(d) { if (d.coauthor == 'False') return "black"; else return "#666"; })

    // flower graph edges
    link[idx] = link_g.selectAll("path")
        .data(links)
      .enter().append("path")
        .attr("id", function(d) { return d.id; })
        .attr("d", function(d) { return linkArc(idx, d, false); })
        .attr("gtype", function(d) { return d.gtype; })
        .attr("class", function(d) { return "link " + d.type; })
        .attr('marker-end', function(d) { return "url(#" + d.gtype+"_"+d.type+"_"+d.id + ")"; })
        .attr("type", function(d) {d.type})
        .style("stroke-width", function (d) { return arrow_width_calc(d.weight)/1.5; })
        .style("stroke", function (d) { if (d.type == "in") return norcolor[0]; else return norcolor[1]; })

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
  if (d.id > 0 && -.5 < d.xpos && d.xpos < .5) shift -= 5;
  if (d.id > 0 && -.3 < d.xpos && d.xpos < .3) shift -= 10;
  if (d.id > 0 && -.1 < d.xpos && d.xpos < .1) shift -= 15;

  // Title
  if (d.id == 0) {
      shift += 30;
  }

  return transform_y(d) + shift
}

function locate_text(d) {
  if (d.xpos < -0.1) return "end";
  else if (d.xpos > 0.1) return "start";
  else return "middle";
}

function arrow_width_calc(weight) {
  if (weight == 0) { return 0; }
  else { return 1+8*weight; }
}

function arrow_size_calc(weight) {
  if (weight == 0) { return 0; }
  else { return 15; }
}
