var selectionTableConfig = {
  tableSettings: {
    "destroy" : true,
    "bAutoWidth" : true,
//    "sScrollY" : "560",
    "bSort" : true,
    "columns": [
    { data: "display-info", className: "dt-body-left"},
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
    "language": {
      "emptyTable": "<div class='table-hint'><b>Your selection</b><br>"
        + "Results you tick appear here. Click one to remove it, then press <b>Go</b> to make the flower.</div>"
    },
      "scrollY": "75vh",
      "scrollCollapse": false
  }
}
