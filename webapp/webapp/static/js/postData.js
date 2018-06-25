function postData (url, data, csrf_token) {
  var data = JSON.stringify(data);
  var form = $('<form display="none" action="' + url + '" method="post">' +
    "<input type='text' name='data' value='" + data + "' />" + csrf_token + 
    '</form>');
  $('body').append(form);
  form.submit();
}

