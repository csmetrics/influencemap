var searchTableConfig = {
    tableSettings: {
      "columns": [
      { title: "Search results", data: "display-info", className: "dt-body-left"},
      { data: "table-id" },
      { data: "data" },
      {
         title: "",
         className: 'details-control',
         orderable: false,
         data: null,
         defaultContent: ''
       },
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
      "select": {
        "style": "multi"
      },
      "language": {
        "emptyTable": "no search result"
      },
      "fixedColumns": true,
      "paging": false, // true,
      "searching": false,
      "sScrollY": 400,
      "ordering": true,
      "order": [[0, "desc" ]],
      "info": true,
      "autoWidth": false,
      "destroy": true,
    }
};

var nestedTableConfig = {
  tableSettings: {
    "pageLength": 10, // default page
    "lengthChange": false,
    "columns": [
    { title: "Paper", data: 'title', className: "index dt-body-left" },
    { title: "Publication year", data: 'year', className: "institution dt-body-right" },
    { title: "Citations", data: 'citations'},
    { title: "", orderable: false, className: 'paper-checkbox', 'render': function (data, type, full, meta){return '<input type="checkbox" checked>'}}
    ],
    "select": {
      "style": "os",
      "selector": 'td:last-child'
    },
    "language": {
      "emptyTable": "no papers found"
    },
    "fixedColumns": true,
    "paging": true,
    "pagingType": "simple_numbers",
    "ordering": true,
    "order": [[2, "desc" ]],
    "info": true,
    "autoWidth": false,
    "destroy": true,
    "searching": false
  },
}
