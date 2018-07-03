///////////////// entity timeline chart /////////////////////
class PubChart {

  constructor(div_id) {
    this.chartsvg = d3.select(div_id).append("svg")
                  .attr("width", "100%");
    this.initflag = false;
  }

  initChart(data, opt) {
    var height = opt.height-opt.top-opt.bottom;
    var width = opt.width-opt.left-opt.right;

    this.g = this.chartsvg.append("g")
        .attr("transform", "translate(" + opt.left + "," + opt.top + ")");
    var x = d3.scaleBand().range([0, width]).padding(0.2);
    var pub_y = d3.scaleLinear().range([height, 0]);

    x.domain(data.map(function(d) { return d.year; }));
    pub_y.domain([0, d3.max(data, function(d) { return d.value; })]);

    // publication chart
    this.g.append("g")
      .attr("class", "axis axis--x")
      .attr("transform", "translate(0," + height + ")")
      .call(d3.axisBottom(x).tickValues(d3.range(opt.min, opt.max, opt.xticks)));

    this.g.append("g")
      .attr("class", "axis axis--y")
      .call(d3.axisLeft(pub_y).ticks(opt.yticks))
    .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 6)
      .attr("dy", "0.71em")
      .attr("text-anchor", "end")
      .text("Number of Publications");

    this.g.selectAll(".bar-pub")
      .data(data)
      .enter().append("rect")
        .attr("class", "bar-pub")
        .attr("id", function(d) { return d.year; })
        .attr("x", function(d) { return x(d.year); })
        .attr("y", function(d) { return pub_y(d.value); })
        .attr("width", x.bandwidth())
        .attr("height", function(d) { return (height-pub_y(d.value)); })
        .style("fill", "#fe3344");

    this.initflag = true;
  }

  isInitialized(){
    return this.initflag;
  }

  updateRange(minyear, maxyear){
    var bars = $(".bar-pub");
    for (var i = 0; i < bars.length; i++) {
      var item = $(bars[i]);
      if (minyear > item.attr("id") || item.attr("id") > maxyear){
        item.css("fill", "#DDD");
      } else {
        item.css("fill", "#fe3344");
      }
    }
  }
}

class CiteChart {

  constructor(div_id) {
    this.chartsvg = d3.select(div_id).append("svg")
                  .attr("width", "100%");
    this.initflag = false;
  }

  isInitialized(){
    return this.initflag;
  }

  initChart(data, opt) {
    var height = opt.height-opt.top-opt.bottom;
    var width = opt.width-opt.left-opt.right;
    this.g = this.chartsvg.append("g")
        .attr("transform", "translate(" + opt.left + "," + opt.top + ")");

    var x = d3.scaleBand().range([0, width]).padding(0.2);
    var cit_y = d3.scaleLinear().range([height, 0]);

    x.domain(data.map(function(d) { return d.year; }));
    cit_y.domain([0, d3.max(data, function(d) { return d.value; })]);

    // citation chart
    this.g.append("g")
      .attr("class", "axis axis--x")
      .attr("transform", "translate(0," + height + ")")
      .call(d3.axisBottom(x).tickValues(d3.range(opt.min, opt.max, opt.xticks)));

    this.g.append("g")
      .attr("class", "axis axis--y")
      .call(d3.axisLeft(cit_y).ticks(opt.yticks))
    .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 6)
      .attr("dy", "0.71em")
      .attr("text-anchor", "end")
      .text("Number of Citations");

    this.g.selectAll(".bar-cite")
      .data(data)
      .enter().append("rect")
      .attr("class", "bar-cite")
      .attr("x", function(d) { return x(d.year); })
      .attr("y", function(d) { return cit_y(d.value); })
      .attr("width", x.bandwidth())
      .attr("height", function(d) { return (height-cit_y(d.value)); })
      .style("fill", "blue");

    this.initflag = true;
  }

  updateRange(data, opt) {
    var vheight = opt.height-opt.top-opt.bottom;
    var vwidth = opt.width-opt.left-opt.right;
    console.log(vheight, vwidth)
    var vx = d3.scaleBand().range([0, vwidth]).padding(0.2);
    var vcit_y = d3.scaleLinear().range([vheight, 0]);
    // this.g.selectAll(".bar-cite").remove();
    this.g.selectAll(".bar-cite")
      .data(data)
      .enter().append("rect")
      .attr("class", "bar-cite")
      .attr("x", function(d) { return vx(d.year); })
      .attr("y", function(d) { return vcit_y(d.value); })
      .attr("width", vx.bandwidth())
      .attr("height", function(d) { return (vheight-vcit_y(d.value)); })
      .style("fill", "blue");
  }
}
