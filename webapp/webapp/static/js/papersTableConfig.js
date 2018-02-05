var  papersTableConfig = {
  author: {
    outerTable: {
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
        ],
  //      "columnDefs": [
  //      {
  //        "targets": 5,
  //        "visible": false
  //      },
  //      ],
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
    innerTable: {
      tableSettings: {
        "pageLength": 10, // default page
        "lengthChange": false,
        "columns": [
        { title: "Papers", className: "index dt-body-left" },
        { title: "Conference", className: "dt-body-left"},
        { title: "Publication year", className: "institution dt-body-right" },
        { title: "ID"},
        { title: "", orderable: false, className: 'paper-checkbox', 'render': function (data, type, full, meta){return '<input type="checkbox" checked>'}}
        ],
  //      "columnDefs": [
  //      {
  //        "targets": [3],
  //        "visible": false
  //      },
  //      ],
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
        "order": [[2, "desc" ]],
        "info": true,
        "autoWidth": false,
        "destroy": true,
        "searching": false
      },
      responseKeys: [
      'title', 'confName', 'year', 'paperID'
      ],
      idCol: 3
    }
  },
  conference: {
    outerTable: {
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
  //      "columnDefs": [
  //      {
  //        "targets": 1,
  //        "visible": false
  //      },
  //      ],
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
        'name', 'numpaper', 'affiliation','field','recentPaper','id'
      ],
      idCol: 1
    },
    innerTable: {
      tableSettings: {
        "pageLength": 10, // default page
        "lengthChange": false,
        "columns": [
        { title: "Papers", className: "index dt-body-left" },
        { title: "Publication year", className: "institution dt-body-right" },
        { title: "ID"},
        { title: "", orderable: false, className: 'paper-checkbox', 'render': function (data, type, full, meta){return '<input type="checkbox" checked>'}}
        ],
  //      "columnDefs": [
  //      {
  //        "targets": [3],
  //        "visible": false
  //      },
  //      ],
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
        "info": true,
        "autoWidth": false,
        "destroy": true,
        "searching": false
      },
      responseKeys: [
        'title', 'year', 'paperID'
      ],
      idCol: 2
    }
  },
  institution: {
    outerTable: {
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
    innerTable: {
      tableSettings: {
        "pageLength": 10, // default page
        "lengthChange": false,
        "columns": [
        { title: "Papers", className: "index dt-body-left" },
        { title: "Publication year", className: "institution dt-body-right" },
        { title: "ID"},
        { title: "", orderable: false, className: 'paper-checkbox', 'render': function (data, type, full, meta){return '<input type="checkbox" checked>'}}
        ],
  //      "columnDefs": [
  //      {
  //        "targets": [3],
  //        "visible": false
  //      },
  //      ],
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
        "info": true,
        "autoWidth": false,
        "destroy": true,
        "searching": false
      },
      responseKeys: [
        'title', 'year', 'paperID'
      ],
      idCol: 2
    }
  }
}

