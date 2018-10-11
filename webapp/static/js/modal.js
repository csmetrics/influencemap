

function make_modal(modal, trigger_element=undefined) {

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close-modal")[0];

// When the user clicks on the button, open the modal 
if (trigger_element != undefined) {
  $(trigger_element).on('click', function() {
    modal.style.display = "block";
  });
}

// When the user clicks on <span> (x), close the modal
span.onclick = function() {
    modal.style.display = "none";
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
}

return function (){modal.style.display="block";}



}
