var searchTableConfig = {
    tableSettings: {
      // "pageLength": 10, // default page
      // "lengthMenu": [ 10, 20, 50, 100 ], // page options
      // "lengthChange": true,
      "columns": [
      { title: "Search results", data: "display-info", className: "dt-body-left"},
      // { data: "entity-type" },
      { data: "table-id" },
      // { data: "name" },
      { data: "data" },
      // { data: "citations" },
      // { data: "affiliation" },
      // { data: "affiliationId" },
      // { data: "papers" },
      // { data: "paperCount" }
      ],
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
      "sScrollY": 560,
      // "pagingType": "simple_numbers",
      "ordering": true,
      "order": [[1, "desc" ]],
      "info": true,
      "autoWidth": false,
      "destroy": true,
    }
}
