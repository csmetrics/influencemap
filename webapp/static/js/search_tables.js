////  --------  Define/initialise varibles  --------  ////

var searchButton = document.getElementById("search-btn");
var continueButton = document.getElementById("continue-btn");
var searchBar = document.getElementById('name-search-bar');
var nestedTableSettings = nestedTableConfig['tableSettings'];

// latest search variables
var latestSearchTerm = "";
var latestSearchOption = $('select[name="type"]').val();

// data tables
var selectiontable = $('#selectiontable').DataTable(selectionTableConfig['tableSettings']);
var searchtable = $('#searchtable').DataTable(searchTableConfig['tableSettings']);



////  --------  Set listeners  --------  ////

$(document).ready(function(){
  if (searchBar.value) {
    search();
  }
});

// ----  Continue button handle ---- //
function setContinueFunction(func){
  continueButton.addEventListener('click', function(){
    func(getSelectedData());
  });
}

// ---- Event handling to remove row from selection ---- //
$('#selectiontable tbody').on('click', 'tr', function () {
   handleSelectionTableRowClick(this);
});

searchButton.addEventListener('click', function(){
  search()
});

searchBar.addEventListener('keypress', function (e) {
  // Search when enter pressed in input bar
  var key = e.which || e.keyCode;
  if (key === 13) { // 13 is enter
    search();
  }
});



////  --------  Define functions  --------  ////

function search(){
  console.log("searching")
  $("#loading").show();
  latestSearchOption = [];
  $(".entity-type-btn.selected-entity").each(function(){
    latestSearchOption.push(this.dataset.entitytype)
  });

  latestSearchTerm = searchBar.value;
  searchtable = makeSearchTable(latestSearchOption);
  $.ajax({
    type: "POST",
    url: "/search",
    data: { "data":
      JSON.stringify({
        keyword: latestSearchTerm,
        option: latestSearchOption,
      })
    },
    success: function (result) { // return data if success
      updateTable(result["entities"], searchtable);
      searchTableEventHandling();
      checkSelectedRows();
      if (latestSearchOption === "author") {addNestedRows();}
      $("#loading").hide();
    },
    error: function (result) {
      console.log("searchButton error");
      $("#loading").hide();
    }
  });
}

function makeSearchTable(entityType){
  if ($.fn.DataTable.isDataTable("#searchtable")) {
    $('#searchtable').DataTable().clear().destroy();
    $('#searchtable').empty();
  }
  var tableSettings = searchTableConfig['tableSettings'];
  return $('#searchtable').DataTable(tableSettings);
}

function updateTable(data, table){
  table.clear();
  for(var i in data) {
    table.row.add(data[i]);
  };
  table.draw();
}

function searchTableEventHandling() {
  $('.papers-outer-checkbox').on('change', function () {
    var tr = $(this).closest('tr');
    var row = searchtable.row( tr );
    var select = this.checked;
    toggleParentRowSelection(row, select);
  })
}

function toggleParentRowSelection(row, select){
  // handle selection table changes
  if (select){
    var newRow = row.data();
    selectiontable.row.add(newRow).draw();
  }
  else {
    removeRowFromSelectionTable(row);
  }
}

function removeRowFromSelectionTable(row){
  selectiontable.rows().nodes().each(function(a) {
    var r = selectiontable.row(a);
    if(r.data()['table-id'] === row.data()['table-id']){
      r.remove().draw();
    }
  });
}

function checkSelectedRows(){
  // select rows in search table if they have already been selected
  console.log("checkSelectedRows called");
  searchtable.rows().nodes().each(function(searchtable_tr_element) {
    selectiontable.rows().nodes().each(function(selectiontable_tr_element) {
      var search_row = searchtable.row(searchtable_tr_element);
      var selection_row = selectiontable.row(selectiontable_tr_element);
      if(search_row.data()['table-id'] === selection_row.data()['table-id']){
        searchtable_tr_element.children[1].children[0].checked = true;
      }
    })
  });
}

function addNestedRows(){
  searchtable.rows().every(function(rowIdx, tableLoop, rowLoop){
    var eid = this.data()['data']['eid'];
    var tableId = this.data()['table-id'];
    var child_text = "<table id='"+tableId+"' class='papers_table compact'></table>";
    this.child(child_text).show();
    var nestedTable = $("#" + tableId);
    nestedTable.closest("td").addClass("innertable");
    //nested_tables[tableId] = {};
    //nested_tables[tableId]['table'] = nestedTable.DataTable(nestedTableSettings);
    //updateTable(this.data()['data']['papers'], nested_tables[tableId]['table']);

    var nestedDataTable= nestedTable.DataTable(nestedTableSettings);
    updateTable(this.data()['data']['papers'], nestedDataTable);
    hideElement(this.child());
  });
  addNestedRowToggle('#searchtable', '.display-info');
}

function addNestedRowToggle (tableSelector, rowSelector){
  $(tableSelector + ' tbody').on('click', rowSelector, function () {
    var tr = $(this).closest('tr');
    var row = searchtable.row( tr );
    var show = !(tr[0].classList.contains('shown'));
   // Close all open rows
    $(tableSelector + ' .shown').each( function (i, elem) {
      var tblRow = searchtable.row( elem );
      elem.classList.remove('shown');
      hideElement(tblRow.child());
    });
    if ( show ) {
        // Open this row
        showElement(row.child());
        tr.addClass('shown');
    }
  });
}

function handleSelectionTableRowClick(element){
  var row = selectiontable.row( element );
  var row_id = row.data()['table-id'];
    $('#searchtable .outer-table-row').each(function(a, b){
      var r = searchtable.row(b);
      if (r.data()['table-id'] === row_id){
        $(b).find('.papers-outer-checkbox').each(function(c, d){
          d.checked = false;
        });
      }
    });
    row.remove().draw();
}

function getSelectedData(){
   var papers = [];
   var names  = [];
   var entities = {"works": [], "authors": [], "sources": [], "institutions": [], "concepts": []};
   var empty_query = true;

   // For each of the selected
   selectiontable.rows().nodes().each(function(a) {
     empty_query = false;
     var datatable_row = selectiontable.row(a).data();
     var type_and_id = datatable_row['table-id'].split('_');
     entities[type_and_id[0]].push(type_and_id[1]);
     var row_data = selectiontable.row(a).data()['data'];
     row_data['entity-type'] = type_and_id[0];

     // If not a paper
     if (row_data['entity-type'] != 'works') {
       // Add names and papers
       names.push(row_data['DisplayName']);
       if ('works' in row_data) {for (var i = 0; i < row_data['works'].length; i++) {
         papers.push(row_data['works'][i]['id']);
       }}
     }
     // Otherwise just pass id
     else {
       names.push(row_data['DisplayName']);
       papers.push(row_data['id']);
     };
   });

   var flower_name = document.getElementById("flowername").value;
   return {'papers': papers, 'flower_name': flower_name, 'names': names, 'entities': entities, 'empty_query': empty_query}
}

function hideElement(elem){
  elem.css({'display': 'none'});
}

function showElement(elem){
  elem.css({'display': 'block'});
}

function clear_search(){
  $("#searchtable").empty();
}

function clear_selection(){
  $("#selectiontable").empty();
}

function clear_search_tables(){
  clear_search();
  clear_selection();
}
