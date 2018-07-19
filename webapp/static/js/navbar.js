var searchBar = document.getElementById('name-search-bar');
var searchButton = document.getElementById('search-btn');

// ----   auto complete   ----
var ac = new autoComplete({
  selector: '#name-search-bar',
  source: function(term, response){
    $.getJSON(
      '/autocomplete?option='+$('select[name="type"').val(),
      { q: term },
      function(data){
        term = term.toLowerCase();
        var choices = data;
        var suggestions = [];
        var maxSuggest = 10;
        var termTokens = term.split(" ");


        for (i = 0; i < choices.length && suggestions.length < maxSuggest; i++) {
          var termInName = true;  // ~choices[i].toLowerCase().indexOf(term)
          for (var termIndex in termTokens){
             if (!(~choices[i].toLowerCase().indexOf(termTokens[termIndex]))){termInName = false}
          }
          var acronymInNameAcroynm = ~toAcronym(choices[i]).toLowerCase().indexOf(term.toLowerCase());

          if (termInName | acronymInNameAcroynm){
              var w = choices[i].split(' ');

              var acronym = toAcronym(choices[i]);

              var st = "";
              if (acronym.length >= 3 & $('select[name="type"').val() !== 'author'){
                st += acronym;
              st += ' - ';
              };
              st += w.join(' ');
              suggestions.push(st);
          }
        }
        response(suggestions);
      });
  },
  onSelect: function(e, term, item){
    if (term.indexOf(" - ") < 0) {
      searchBar.value = term;
    } else {
      searchBar.value = term.split(" - ")[1]
    };

    redirectAndSearch();
  }
});


function toAcronym(name){
words_to_rm = ['of', 'the', 'and', 'on', 'for']
var w = name.split(' ');
var primary_words = [];
st = '';
for (var j in w){if (words_to_rm.indexOf(w[j]) < 0){primary_words.push(w[j])}};
  var st = "";
  if (primary_words.length >= 3){
    for (var word in primary_words){
       st += primary_words[word].charAt(0).toUpperCase()
    };
  }
return st;
}


function redirectAndSearch(){
  var keyword = searchBar.value;
  var option = $(".entity-option:checked").val();
  console.log("redirectAndSearch", keyword, option);
  postData('/create', {'keyword': keyword, 'option': option, 'search': 'true'});

}



// searchButton.addEventListener('click', function(){
//   redirectAndSearch();
// });


// Search when enter pressed in input bar
// searchBar.addEventListener('keypress', function (e) {
//   var key = e.which || e.keyCode;
//   if (key === 13) { // 13 is enter
//     redirectAndSearch(false, true);
//   }
// });
