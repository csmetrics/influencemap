var selectionTableConfig = {
  tableSettings: {
    "destroy" : true,
    "bAutoWidth" : true,
    "sScrollY" : "400",
    "bSort" : true,
    "columns": [
      { title: "Name", data: "name", className: "index dt-body-center"},
      { title: "Citations", data: "citations", className: "institution dt-body-right"},
      { title: "Affiliation", data: "affiliation", className: "dt-body-center"},
      { title: "ID", data: "eid"},
      { title: "Selected", data: "display text", className: "dt-body-left"},
      { title: "Name_ID", data: "name_id"}
    ],
    "columnDefs": [
        {
        "targets": [0,1,2,3,5],
        "visible": false
        },
     ],
    "searching": false,
    "paging": false,
  }
}
