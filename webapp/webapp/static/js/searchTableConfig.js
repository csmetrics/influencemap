var searchTableConfig = {
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
      { title: "ID"}
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
    'name', 'numpaper', 'affiliation','field','recentPaper','authorID'
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
      { title: "ID"}
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
      "order": [[0, "asc" ]],
      "info": true,
      "autoWidth": false,
      "destroy": true,
    },
    responseKeys: [
    'name', 'id'
    ],
    idCol: 1
  },
  institution: {
    tableSettings: {
      "pageLength": 10, // default page
      "lengthMenu": [ 10, 20, 50, 100 ], // page options
      "lengthChange": true,
      "columns": [
      { title: "Name", className: "index dt-body-center" },
      { title: "ID"}
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
      "order": [[0, "asc" ]],
      "info": true,
      "autoWidth": false,
      "destroy": true,
    },
    responseKeys: [
    'name', 'id'
    ],
    idCol: 1
  },
  journal: {
    tableSettings: {
      "pageLength": 10, // default page
      "lengthMenu": [ 10, 20, 50, 100 ], // page options
      "lengthChange": true,
      "columns": [
      { title: "Name", className: "index dt-body-center" },
      { title: "ID"}
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
      "order": [[0, "asc" ]],
      "info": true,
      "autoWidth": false,
      "destroy": true,
    },
    responseKeys: [
    'name', 'id'
    ],
    idCol: 1
  }
};
