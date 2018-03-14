var searchTableConfig = {
  author: {
    tableSettings: {
      // "pageLength": 10, // default page
      // "lengthMenu": [ 10, 20, 50, 100 ], // page options
      // "lengthChange": true,
      "columns": [
      // { title: "Search results", data: "display-info", className: "dt-body-left"},
      // { data: "entity-type"},
      { title: "Name", data: "name", className: "index dt-body-center" },
      { title: "Citations", data: "citations", className: "institution dt-body-right" },
      { title: "Affiliation", data: "affiliation", className: "dt-body-center" },
      { title: "ID", data: "eid"}
      ],
     // "columnDefs": [
     // {
     //   "targets": [],
     //   "visible": false
     // },
     // ],
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
      // "pagingType": "simple_numbers",
      "ordering": true,
      "order": [[1, "desc" ]],
      "info": true,
      "autoWidth": false,
      "destroy": true,
    },
    responseKeys: [
    'name', 'citationCount', 'affiliation','eid'
    ], 
  }
}
//   institution: {
//     tableSettings: {
//       // "pageLength": 10, // default page
//       // "lengthMenu": [ 10, 20, 50, 100 ], // page options
//       // "lengthChange": true,
//       "columns": [
//       { title: "Search results", data: "display-info", "dt-body-left"},
//       { data: "entity-type"},
//       { data: "name"},
//       { data: "eid"}
//       ],
//      "columnDefs": [
//      {
//        "targets": [1, 2, 3],
//        "visible": false
//      },
//      ],
//       "select": {
//         "style": "multi"
//       },
//       "language": {
//         "emptyTable": "no search result"
//       },
//       "fixedColumns": true,
//       "paging": false, // true,
//       "searching": false,
//       "sScrollY": 400,
//       // "pagingType": "simple_numbers",
//       "ordering": true,
//       "order": [[1, "desc" ]],
//       "info": true,
//       "autoWidth": false,
//       "destroy": true,
//     },
//     responseKeys: [
//     'name', 'eid'
//     ], 
//   },
//   conference: {
//     tableSettings: {
//       // "pageLength": 10, // default page
//       // "lengthMenu": [ 10, 20, 50, 100 ], // page options
//       // "lengthChange": true,
//       "columns": [
//       { title: "Search results", data: "display-info", "dt-body-left"},
//       { data: "entity-type"},
//       { data: "name"},
//       { data: "eid"}
//       ],
//      "columnDefs": [
//      {
//        "targets": [1, 2, 3],
//        "visible": false
//      },
//      ],
//       "select": {
//         "style": "multi"
//       },
//       "language": {
//         "emptyTable": "no search result"
//       },
//       "fixedColumns": true,
//       "paging": false, // true,
//       "searching": false,
//       "sScrollY": 400,
//       // "pagingType": "simple_numbers",
//       "ordering": true,
//       "order": [[1, "desc" ]],
//       "info": true,
//       "autoWidth": false,
//       "destroy": true,
//     },
//     responseKeys: [
//     'name', 'eid'
//     ], 
//   },
//     journal: {
//     tableSettings: {
//       // "pageLength": 10, // default page
//       // "lengthMenu": [ 10, 20, 50, 100 ], // page options
//       // "lengthChange": true,
//       "columns": [
//       { title: "Search results", data: "display-info", "dt-body-left"},
//       { data: "entity-type"},
//       { data: "name"},
//       { data: "eid"}
//       ],
//      "columnDefs": [
//      {
//        "targets": [1, 2, 3],
//        "visible": false
//      },
//      ],
//       "select": {
//         "style": "multi"
//       },
//       "language": {
//         "emptyTable": "no search result"
//       },
//       "fixedColumns": true,
//       "paging": false, // true,
//       "searching": false,
//       "sScrollY": 400,
//       // "pagingType": "simple_numbers",
//       "ordering": true,
//       "order": [[1, "desc" ]],
//       "info": true,
//       "autoWidth": false,
//       "destroy": true,
//     },
//     responseKeys: [
//     'name', 'eid'
//     ], 
//   },
// }