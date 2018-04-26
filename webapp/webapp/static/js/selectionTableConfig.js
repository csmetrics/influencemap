var selectionTableConfig = {
  tableSettings: {
    "destroy" : true,
    "bAutoWidth" : true,
    "sScrollY" : "560",
    "bSort" : true,
    "columns": [
    { title: "Selected", data: "display-info", className: "dt-body-left"},
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
    "searching": false,
    "paging": false,
    "info": false,
  }
}
