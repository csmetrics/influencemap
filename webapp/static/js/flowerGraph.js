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
    numnodes = [], svg = [], simulation = [],
    bar_axis_x = [], bar_axis_y = [],
    node_in = [], node_out = [],
    text_in = [], text_out = [];

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
    var nodes = data["nodes"];
    var links = data["links"];
    var bars = data["bars"];

    h_margin = 225;
    v_margin = 250;
    yheight = 100;
    flower_margin = 0;

    svg[idx] = d3.select(svg_id),
    width = w, magf = Math.min(250, width/5),
    height = 650,
    numnodes[idx] = nodes.length,
    center = [width/2, height/2 - flower_margin];
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
        .attr("class", "hl-text")
        .call(d3.axisBottom(x))
        .selectAll("text")
          .text(function(d) { if (d.length > 20) return d.slice(0, 20)+"..."; else return d.slice(0, 20); })
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
          .attr("dy", "-.5em")
          .attr("transform", "rotate(-90)");;

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
        .attr("refX", function (d) { return 10+10*d.padding; })
        .attr("refY", 0)
        .attr("markerWidth", function (d) { return arrow_size_calc(d.weight); })
        .attr("markerHeight", function (d) { return arrow_size_calc(d.weight); })
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
        .attr("markerWidth", function (d) { return arrow_size_calc(d.weight); })
        .attr("markerHeight", function (d) { return arrow_size_calc(d.weight); })
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
        .style("stroke-width", function (d) { return arrow_width_calc(d.weight); })
        .style("stroke", function (d) { if (d.type == "in") return norcolor[0]; else return norcolor[1]; })
        .on("mouseover", function() { highlight_on(idx, this); })
        .on("mouseout", function() { highlight_off(idx); });

    // flower graph nodes
    node_in[idx] = svg[idx].append("g").selectAll("circle")
        .data(nodes)
      .enter().append("circle")
        .attr("id", function(d) { return d.id; })
        .attr("class", "hl-circle")
        .attr("gtype", function(d) { return d.gtype; })
        .attr("r", function(d) { return 5+10*d.size; })
        .style("fill", function (d, i) {if (d.id == 0) return "#ccc"; else return colors(d.weight);})
        .style("stroke", function (d, i) { if ((d.coauthor == 'True') && (d.id != 0)) return "green";
                                          else return ""; })
        .style("stroke-width", 2)
        .on("mouseover", function() { highlight_on(idx, this); })
        .on("mouseout", function() { highlight_off(idx); })
        .on("click", function(d) { toggle_split(idx, this); });

    // flower graph nodes
    node_out[idx] = svg[idx].append("g").selectAll("circle")
        .data(nodes)
      .enter().append("circle")
        .attr("id", function(d) { return d.id; })
        .attr("class", "hl-circle")
        .attr("gtype", function(d) { return d.gtype; })
        .attr("r", function(d) { return 5+10*d.size; })
        .style("fill", function (d, i) {if (d.id == 0) return "#ccc"; else return colors(d.weight);})
        .style("stroke", function (d, i) { if ((d.coauthor == 'True') && (d.id != 0)) return "green";
                                          else return ""; })
        .style("stroke-width", 2)
        .style("cursor", "pointer")
        .on("mouseover", function() { highlight_on(idx, this); })
        .on("mouseout", function() { highlight_off(idx); })
        .on("click", function(d) { toggle_split(idx, this); showNodeData(idx, this);});

    // flower graph node text
    text_in[idx] = svg[idx].append("g").selectAll("text")
        .data(nodes)
      .enter().append("text")
        .attr("id", function(d) { return d.id; })
        .attr("class", "hl-text")
        .attr("gtype", function(d) { return d.gtype; })
        .attr("x", 8)
        .attr("y", ".31em")
        .text(function(d) { return d.name; })
        .style("fill", function(d) { if (d.coauthor == 'False') return "black"; else return "gray"; });
//        .style("font-style", function(d) { if (d.coauthor == 'False') return "normal"; else return "italic"; });

    // flower graph node text
    text_out[idx] = svg[idx].append("g").selectAll("text")
        .data(nodes)
      .enter().append("text")
        .attr("id", function(d) { return d.id; })
        .attr("class", "hl-text")
        .attr("gtype", function(d) { return d.gtype; })
        .attr("x", 8)
        .attr("y", ".31em")
        .text(function(d) { d.name; })
        .style("fill", function(d) { if (d.coauthor == 'False') return "black"; else return "gray"; });
//        .style("font-style", function(d) { if (d.coauthor == 'False') return "normal"; else return "italic"; });

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
  if (id == 0) return;

  // highlight rectangles
  svg[idx].selectAll("rect").each(function() {
    if (d3.select(this).attr("class") == "bar") {
        d3.select(this).style("opacity", function (d) { if(id != d.id && d.id != 0 && group == d.gtype) return 0.4; else return 1; });
    }
  });

  // highlight text
  svg[idx].selectAll("text").each(function() {
    if (d3.select(this).attr("class") == "hl-text") {
        d3.select(this).style("opacity", function (d) { if(id != d.id && d.id != 0 && group == d.gtype) return 0.4; else return 1; });
    }
  });

  // highlight circles
  svg[idx].selectAll("circle").each(function() {
    if (d3.select(this).attr("class") == "hl-circle") {
        d3.select(this).style("opacity", function (d) { if(id != d.id && d.id != 0 && group == d.gtype) return 0.4; else return 1; });
    }
  });

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

  // un-highlight rectangles
  svg[idx].selectAll("rect").each(function() {
    if (d3.select(this).attr("class") == "bar") {
        d3.select(this).style("opacity", 1);
    }
  });

  // un-highlight text
  svg[idx].selectAll("text").each(function() {
    if (d3.select(this).attr("class") == "hl-text") {
        d3.select(this).style("opacity", 1);
    }
  });

  // un-highlight circles
  svg[idx].selectAll("circle").each(function() {
    if (d3.select(this).attr("class") == "hl-circle") {
        d3.select(this).style("opacity", 1);
    }
  });
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
  d.fx = center[0]+magf*d.xpos;
  return d.x
}

function transform_y(d) {
  d.fy = center[1]+magf*d.ypos;
  return d.y
}

function transform_text_x(d) {
  shift = 0;
  circ_dif = 5;
  d.fx = center[0]+magf*d.xpos;

  if (d.xpos < -.3) shift -= 5 + 10 * d.size + circ_dif;
  if (d.xpos > .3) shift += 5 + 10 * d.size + circ_dif;
  return d.x + shift
}

function transform_text_y(d) {
  shift = 0;
  d.fy = center[1]-magf*d.ypos;

  if (d.id > 0 && -.5 < d.xpos && d.xpos < .5) shift -= 5;
  if (d.id > 0 && -.4 < d.xpos && d.xpos < .4) shift -= 6;
  if (d.id > 0 && -.3 < d.xpos && d.xpos < .3) shift -= 11;
  if (d.id > 0 && -.1 < d.xpos && d.xpos < .1) shift -= 15;
  return d.y + shift
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
            .attr("transform", "translate(" + eval(-shift) + ", 0)");
    });

  // Move text wrt shift
  text_out[idx].transition()
    .each(function() {
        d3.select(this).transition()
            .duration(2000)
            .attr("transform", "translate(" + shift + ", 0)");
    });

  // Move nodes wrt shift
  node_in[idx].transition()
    .each(function() {
        d3.select(this).transition()
            .duration(2000)
            .attr("transform", "translate(" + eval(-shift) + ", 0)");
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

/*
function populateNodeInfoContent(data){
  var container_div = document.getElementById("node_info_container");
  var content_div = document.getElementById("node_info_content");
  container_div.removeChild(content_div);
  var references = data["reference_papers"];
  var citations = data["citation_papers"];
  var refs_shown = Math.min(3, references.length);
  var cites_shown = Math.min(3, citations.length);

  var title = "<h3>"+data["node_name"]+"</h3>";

  // build references string
  var references_string = "";
  if (refs_shown !== 0){
    var references_header = "<span><i><span style='color: rgb(228,130,104)'>cited by</span></i></span>";
    var references_body = "<ul>";
    for (i = 0; i< refs_shown;i++){
      //references_body += "<li><i>"+references[i]["link_title"]+"</i>, "+references[i]["link_year"]+"</li>";
      references_body += genNodeInfoListElement(references[i]);
    }
    references_body += "</ul>";
    references_string += references_header+references_body;
  }

  // build citations string
  var citations_string = "";
  if (cites_shown !== 0){
    var citations_header = "<span><i><span style='color: rgb(107, 172, 208)'>referenced</span></i></span>";
    var citations_body = "<ul>";
    for (i = 0; i< cites_shown;i++){
      citations_body += genNodeInfoListElement(citations[i]);
    }
    citations_body += "</ul>";
    citations_string += citations_header+citations_body;
  }

  var html_string = "<div id='node_info_content'>"+title+references_string+citations_string+"</div>";
  var html_elem = new DOMParser().parseFromString(html_string, 'text/html').body.childNodes;
  container_div.appendChild(html_elem[0]);
}
*/


function populateNodeInfoContent(data){
  var container_div = document.getElementById("node_info_container");
  var content_div = document.getElementById("node_info_content");
  container_div.removeChild(content_div);
  var references = data["References"];
  var citations = data["Citations"];
  var refs_shown = Math.min(3, references.length);
  var cites_shown = Math.min(3, citations.length);
  var entities = data.entity_names;
  var title = "<h3>"+data["node_name"]+"</h3>";

  // build references string
  var references_table = "";
  if (refs_shown !== 0){
    var references_header = "<span><i><span style='color: rgb(107,172,208)'>References</span></i></span>";

    references_table += references_header + "<table>";

    for (var i=0; i<references.length;i++){
      var left = formatCitation(references[i]["to"],data.entity_names);
      for (var j = 0; j< references[i]["from"].length;j++){
        var right = (formatCitation(references[i]["from"][j],entities));
        if (j == 0) references_table += "<tr><td width='49%'rowspan='"+references[i]["from"].length+"'>"+left+"</td><td width='2%' style='color: rgb(107,172,208); font-size: 30px'>⟵</td><td width='49%'>"+right+"</td></tr>";
        else references_table += "<tr><td width='2%'style='color: rgb(107,172,208); font-size: 30px'>⟵</td><td width='49%'>"+right+"</td></tr>";
      }
    }   
    references_table += "</table>";

  }

  // build citations string
  var citations_table = "";
  if (cites_shown !== 0){
    var citations_header = "<span><i><span style='color: rgb(228,130,104)'>Citations</span></i></span>";
    citations_table += citations_header + "<table>";

    for (var i=0; i<citations.length;i++){
      var left = formatCitation(citations[i]["from"],data.entity_names);
      for (var j = 0; j< citations[i]["to"].length;j++){
        var right = (formatCitation(citations[i]["to"][j],entities));
        if (j == 0) citations_table += "<tr><td width='49%' rowspan='"+citations[i]["to"].length+"'>"+left+"</td><td width='2%' style='color: rgb(228,130,104); font-size: 30px'>⟶ </td><td width='49%'>"+right+"</td></tr>";
        else citations_table += "<tr><td width='2%' style='color: rgb(228,130,104); font-size: 30px'>⟶ </td><td width='49%'>"+right+"</td></tr>";
      }
    }
    citations_table += "</table>";

  }

  var html_string = "<div id='node_info_content'>"+title+references_table+citations_table+"</div>";
  var html_elem = new DOMParser().parseFromString(html_string, 'text/html').body.childNodes;
  container_div.appendChild(html_elem[0]);
}


// rgb(107, 172, 208); blue
//  rgb(228, 130, 104);oranger

function getData(param){
  var name = param['name'];
  var data_dict = { // input to the views.py - search()
      "name": name
    };
    var t0 = performance.now();
  $.ajax({
    type: "POST",
    url: "/get_node_info/",
    data: {"data_string": JSON.stringify(data_dict)},
    success: function (result) { // return data if success
      console.log(result);
//      console.log(result.node_info);
      result["node_name"] = name;
      populateNodeInfoContent(result);
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
    var data = getData({"name": name});
}

function hideNodeData(){
    document.getElementById('node_info_modal').style.display = "none";
}
