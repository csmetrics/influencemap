/*  ---    HTML ELEMENTS    ---   */

var save_btn_html_string = '<input id="cache-btn" type="submit" value="Save" float="bottom" class="btn medium" style="width:100%; margin-top:10px" />';
var save_btn_html_elem = new DOMParser().parseFromString(save_btn_html_string, 'text/html').body.childNodes;
var selection_table_container = document.getElementById('selectiontable-container');
selection_table_container.appendChild(save_btn_html_elem[0]);

var modal_html_string = " \
<div id='myModal' class='modal'> \
  <!-- Modal content --> \
  <div class='modal-content  right'> \
    <span class='close'>&times;</span> \
    <div id='cache-type-selection' class='hoc cntr' style='padding: 10px'> \
      <button id='cache-author' class='btn'>Author</button> \
      <button id='cache-group' class='btn'>Group</button> \
    </div> \
    <div id='cache-author-div' class='hoc cntr'> \
      <form action='javascript:cacheAuthor();' id=cacheAuthorForm'> \
        <input type='radio' name='typeAuthor' value='anu_researchers' checked> ANU Researcher<br> \
        <input type='radio' name='typeAuthor' value='turing_award_winners'> Turing Award Winner<br> \
        <input type='radio' name='typeAuthor' value='fields_medalists'> Fields Medalist<br> \
        Year:<br> \
        <input id='yearAuthor' type='text' name='year'><br> \
        Citation:<br> \
        <input id='citationAuthor' type='text' name='citation'><br> \
        Affiliation:<br> \
        <input id='affiliationAuthor' type='text' name='affiliation'><br> \
        Name:<br> \
        <input id='nameAuthor' type='text' name='name'><br> \
        Normalised Name:<br> \
        <input id='normalizedNameAuthor' type='text' name='normalizedName'><br> \
        Keywords:<br> \
        <input id='keywordsAuthor' type='text' name='keywords'><br> \
        URL:<br> \
        <input id='urlAuthor' type='text' name='url'><br> \
        <button type='submit' class='btn btn-primary mb-2'>Confirm identity</button> \
      </form> \
    </div> \
    <div id='cache-group-div' class='hoc cntr'> \
      <form action='javascript:cacheGroup();' id='cacheGroupForm'> \
        <input type='radio' name='typeGroup' value='conference' checked> Conference<br> \
        <input type='radio' name='typeGroup' value='journal'> Journal<br> \
        <input type='radio' name='typeGroup' value='university-group'> University Group<br> \
        <input type='radio' name='typeGroup' value='project'> Project \
        Name:<br> \
        <input id='nameGroup' type='text' name='name'><br> \
        Normalized Name:<br> \
        <input id=normalizedNameGroup' type='text' name='normalizedName'><br> \
        Year:<br> \
        <input id='yearGroup' type='text' name='name'><br> \
        Fields:<br> \
        <input id='fieldsGroup' type='text' name='fields'><br> \
        <button type='submit' class='btn btn-primary mb-2'>Save</button> \
      </form> \
    </div> \
  </div> \
</div>";

var modal_html_elem = new DOMParser().parseFromString(modal_html_string, 'text/html').body.childNodes;
document.body.appendChild(modal_html_elem[0]);


/*  ---    MODAL    ---   */
var cacheAuthorDiv = document.getElementById('cache-author-div');
var cacheGroupDiv = document.getElementById('cache-group-div');
var cacheAuthorForm = document.getElementById('cacheAuthorForm');
var cacheGroupForm = document.getElementById('cacheGroupForm');

// Get the modal
var modal = document.getElementById('myModal');

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];

// When the user clicks on <span> (x), close the modal
span.onclick = function() {
    modal.style.display = "none";
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    console.log("closed by window click")}
}
document.getElementById('cache-author').addEventListener('click',function(){
  cacheGroupDiv.style.display="none";
  cacheAuthorDiv.style.display="block";

});
document.getElementById('cache-group').addEventListener('click',function(){
  cacheGroupDiv.style.display="block";
  cacheAuthorDiv.style.display="none";

});
document.getElementById('cache-btn').addEventListener('click',function(){
  modal.style.display = "block";
  cacheGroupDiv.style.display="none";
  cacheAuthorDiv.style.display="none";

});


/*  ---    POST DATA FOR CACHE    ---   */
function cacheAuthor(){
  var data = {};
  var selected_keys = Object.keys(selected_data);
  var authorIds = [];
  for (i in selected_keys){
    authorIds.push(selected_keys[i].split('_')[1])
  };
  data['AuthorIds'] = authorIds;
  data['Year'] = $('#yearAuthor').val();
  data['DisplayName'] = $('#nameAuthor').val();
  data['NormalizedName'] = $('#normalizedNameAuthor').val();
  data['Citation'] = $('#citationAuthor').val();
  data['Keywords'] = $('#keywordsAuthor').val().split(',');
  data['Type'] = $("input[name='typeAuthor']:checked").val();
  data['Url'] = $('#urlAuthor').val();
  data['Affiliation'] = $('#affiliationAuthor').val();
  console.log(data);


  $.ajax({
    type: "POST",
    url: "/manualcache",
    data: { // input to the views.py - search()
      ent_data: JSON.stringify(data),
      type: 'author',
    },
    success: function (result) { // return data if success
      location.reload();
    },
    error: function (result) {
      console.log("error saving cache");
    }
  });


console.log('cacheAuthor called')
}

function cacheGroup(){ // NOT YET IMPLEMENTED
console.log('cacheGroup called')
}
