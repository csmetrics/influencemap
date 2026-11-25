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
        // Shown before the first search. search_tables.js swaps this for
        // a "searching" / "no results" message once a search has run.
        "emptyTable": "<div class='table-hint'><b>Search to get started</b>"
          + "<ol><li>Choose what to search for above: authors, institutions, sources or papers.</li>"
          + "<li>Type a name in the search bar and press Enter.</li>"
          + "<li>Tick the results you want in your flower.</li></ol>"
          + "<a href='#' class='open-instructions'><i class='far fa-question-circle'></i> Watch a step-by-step demo</a></div>"
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
