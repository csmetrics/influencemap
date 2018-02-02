var  papersTableConfig= {
  author: {
    tableSettings: {
      "pageLength": 10, // default page
      "lengthMenu": [ 10, 20, 50, 100 ], // page options
      "lengthChange": true,
      "columns": [
      { title: "Name", className: "index dt-body-center" },
      { title: "Number of papers", className: "institution dt-body-right" },
      { title: "Affiliations", className: "dt-body-center" },
      { title: "Field (number of papers)", className: "field dt-body-left" },
      { title: "Most recent paper", className: "dt-body-left" },
      { title: "ID"},
/*      { // expand button
       title: "",
        className: 'details-control',
        orderable: false,
        data: null,
        defaultContent: ''
      }
*/      ],
      "columnDefs": [
      {
        "targets": 5,
        "visible": false
      },
      ],
      "createdRow": function(row, data, index) { $(row).addClass("outer-table-row") },
      "select": {
        "style": "multi"
      },
      "language": {
        "emptyTable": "no search result"
      },
      "fixedColumns": true,
      "paging": true,
      "pagingType": "simple_numbers",
      "ordering": true,
      "order": [[1, "desc" ]],
      "info": true,
      "autoWidth": false,
      "destroy": true,
    },
    responseKeys: [
    'name', 'numpaper', 'affiliation','field','recentPaper','id'
    ], 
    idCol: 5
  },
  conference: {
    tableSettings: {
      "pageLength": 10, // default page
      "lengthMenu": [ 10, 20, 50, 100 ], // page options
      "lengthChange": true,
      "columns": [
      { title: "Name", className: "index dt-body-center" },
      { title: "Number of papers", className: "institution dt-body-right" },
      { title: "Affiliations", className: "dt-body-center" },
      { title: "Field (number of papers)", className: "field dt-body-left" },
      { title: "Most recent paper", className: "dt-body-left" },
      { title: "ID"},
      { // expand button
       title: "",
        className: 'details-control',
        orderable: false,
        data: null,
        defaultContent: ''
      }
      ],
      "columnDefs": [
      {
        "targets": 5,
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
      "paging": true,
      "pagingType": "simple_numbers",
      "ordering": true,
      "order": [[1, "desc" ]],
      "info": true,
      "autoWidth": false,
      "destroy": true,
    },
    responseKeys: [
    'name', 'numpaper', 'affiliation','field','recentPaper','id'
    ],
    idCol: 5
  },
  institution: {
    tableSettings: {
      "pageLength": 10, // default page
      "lengthMenu": [ 10, 20, 50, 100 ], // page options
      "lengthChange": true,
      "columns": [
      { title: "Name", className: "index dt-body-center" },
      { title: "ID"},
      { // expand button
       title: "",
        className: 'details-control',
        orderable: false,
        data: null,
        defaultContent: ''
      }
      ],
      "columnDefs": [
      {
        "targets": 1,
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
      "paging": true,
      "pagingType": "simple_numbers",
      "ordering": true,
      "order": [[0, "desc" ]],
      "info": true,
      "autoWidth": false,
      "destroy": true,
    },
    responseKeys: [
    'name', 'id'
    ],
    idCol: 1
  },
  all: {
    tableSettings: {
      "pageLength": 10, // default page
      "lengthChange": false,
      "columns": [
      { title: "Papers", className: "index dt-body-left" },
      { title: "Publication year", className: "institution dt-body-right" },
      { title: "ID"},
      { title: "", orderable: false, className: 'paper-checkbox', 'render': function (data, type, full, meta){return '<input type="checkbox" checked>'}}
      ],
      "columnDefs": [
      {
        "targets": [2],
        "visible": false
      },
      ],
      "select": {
        "style": "os", 
        "selector": 'td:last-child'
      },
      "language": {
        "emptyTable": "no search result"
      },
      "fixedColumns": true,
      "paging": true,
      "pagingType": "simple_numbers",
      "ordering": true,
      "order": [[1, "desc" ]],
//      "info": true,
      "autoWidth": false,
      "destroy": true,
      "searching": false
    },
    responseKeys: [
    0,1,2
    ],
    idCol: 2
  },

};

