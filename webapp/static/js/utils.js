function normaliseNameForCitation(name){
  var nametokens = name.split(' ');
  if (nametokens.length === 0){return};
  var lastname = toTitleCase(nametokens[nametokens.length - 1]);
  if (nametokens.length === 1){return lastname}
  var firstname = toTitleCase(nametokens[0]);
  var firstinitial = firstname[0];
  return firstinitial + ". " + lastname;
}

function toTitleCase(str) {
  // credit to G.Dean and J. Freed at stackoverflow.com/questions/196972/convert-string-to-title-case-with-javascript
    return str.replace(
        /\w\S*/g,
        function(txt) {
            return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
        }
    );
}


var journal_format_list = {
  'arxiv': 'arXiv',
};


function formatJournal(journal_name) {
  var format_name = [];
  var words = journal_name.split(' ');
  for (i in words) {
    if (words[i] in journal_format_list) {
      format_name.push(journal_format_list[words[i]]);
    }
    else {
      format_name.push(toTitleCase(words[i]));
    }
  }

  return format_name.join(" ");
}


function formatCitation(paper, authorsToHighlight=[], node_name){
  var authors = paper["Authors"];
  authors = authors.sort(function(a, b) {return a['AuthorOrder'] - b['AuthorOrder']});

  var names = [];
  for (i in authors){
    var formatted_name = normaliseNameForCitation(authors[i]["AuthorName"]);
    names.push({"AuthorName": authors[i]["AuthorName"], "FormattedName": formatted_name, "AuthorId": authors[i]["AuthorId"]});
  }
  out_str = [];
  for (i in names){
    var a = names[i];
    if (authorsToHighlight.indexOf(a["AuthorName"]) >= 0){a["FormattedName"] = "<b>"+a["FormattedName"]+"</b>"};
    if ("AffiliationName" in a) {
      a["FormattedName"] = "<span"+
                            " data-toggle='tooltip'"+
                            " data-delay='{\"hide\": 500, \"show\": 700}'"+
                            " data-html='true'"+
                            " data-placement='bottom'"+
                            " title='<a href=\"https://academic.microsoft.com/#/detail/"+a["AffiliationId"]+"\" style=\"color: #fff;\">"   +a["AffiliationName"]+   "</a>'"+
                           ">"+
                             a["FormattedName"]+
                           "</span>";
    }
    out_str.push("<a class='node_info_a' href=\"https://academic.microsoft.com/#/detail/"+a["AuthorId"]+"\">"+a["FormattedName"]+"</a>");
  }

  var venue = "";
  if ("JournalName" in paper) {
    venue = ", <a class='node_info_a' href='https://academic.microsoft.com/#/detail/";
    venue += paper["JournalId"] + "'>";
    venue += formatJournal(paper["JournalName"]) + "</a>";
  }
  if ((node_name != paper["JournalName"]) && ("ConferenceName" in paper)) {
      venue = ",  <a class='node_info_a' href='https://academic.microsoft.com/#/detail/";
      venue += paper["ConferenceSeriesId"] + "'>";
      venue += paper["ConferenceName"].toUpperCase() + "</a>";
  }

  return out_str.join(', ') + ". <i><a class='node_info_a' href=\"https://academic.microsoft.com/#/detail/"+paper["PaperId"]+"\">"+toTitleCase(paper["PaperTitle"]) + "</a></i>, " + paper["Year"] + venue;
}
