var emptytablemsg = "<div class='emb-table'>"+
  "<h3><b>Create your own flowers</b></h3>"+
  "<ol><li>Select the type(s) of entity you want to search for.</li>"+
  "<li>Enter the name or keyword you would like to search for.</li>"+
  "<li>Use the information to identify entities that you want to include in your flower.</li>"+
  "<li>Repeat until you have selected all entities you want included in your flower.</li>"+
  "<li>(Optional) Name your flower.</li>"+
  "<li>Press <b>Go</b> to create your flower, but be patient, computation time depends on the selected entities.</li></ol></div>";

var searchTableConfig = {
    tableSettings: {
      "columns": [
      { data: "display-info", className: "dt-body-left display-info"},
      { data: "table-id" },
      { data: "data" },
      {
        orderable: false,
        data: null,
        'render': function (data, type, full, meta){
          return '<input type="checkbox" class="papers-outer-checkbox">'
        }
      }
      ],
     "createdRow": function(row, data, index) {
        $(row).addClass("outer-table-row")
      },
     "columnDefs": [
     {
       "targets": [1,2],
       "visible": false
     },
     ],
      // "select": {
      //   "style": "multi",
      //   "selector": 'td:last-child input[type="checkbox"]'
      // },
      "language": {
        "emptyTable": emptytablemsg
      },
      "fixedColumns": true,
      "paging": false, // true,
      "searching": false,
//      "sScrollY": 560,
      // "pagingType": "simple_numbers",
      "ordering": false,//true,
    //  "order": [[0, "desc" ]],
      "info": false,
      "autoWidth": false,
      "destroy": true,
      "scrollY": "85vh",
      "scrollCollapse": false
    },
};

var nestedTableConfig = {
  tableSettings: {
    // "pageLength": 10, // default page
    "lengthChange": false,
    "columns": [
    { title: "Paper", data: 'title', className: "index dt-body-left" },
    { title: "Publication year", data: 'year', className: "institution dt-body-right" },
    { title: "Citations", data: 'citations'},
    ],
    // "select": {
    //   "style": "os",
    //   "selector": 'td:last-child input[type="checkbox"]'
    // },
    "language": {
      "emptyTable": "no papers found"
    },
    "fixedColumns": true,
    "paging": false,
    // "pagingType": "simple_numbers",
    "ordering": true,
    "order": [[2, "desc" ]],
    "info": true,
    'autoHeight': true,
    "autoWidth": false,
    "destroy": true,
    "searching": false,
    'background': 'transparent',
  },
}
