var progressGroup = document.getElementById("progress-group");
var progressText = document.getElementById("progress-text");
var progressNumber = document.getElementById("progress-number");
var progressBar = document.getElementById("progress-bar");
var flag = false;
var percent = 0;
var message = "";

function showProgressBar() {
  percent = 0;
  message = "start searching"
  flag = true;
  progressText.innerText = message;
  progressNumber.innerText = percent+"%";
  progressBar.style.width = percent+"%";
  console.log("showProgressBar", percent, flag);
  progressGroup.classList.remove("invisible");
  window.setTimeout(updateProgressBar, 1000);
}
function hideProgressBar() {
  flag = false;
  console.log("hideProgressBar", percent, flag);
  progressGroup.classList.add("invisible");
}

function updateProgressBar(ptype){
  $.ajax({
    type: "POST",
    url: "/progress",
    data: {
        type: ptype
    },
    success: function (result) {
      console.log("updateProgressBar success");
      console.log(result["msg"], result["percent"]);
      percent = result["percent"];
      message = result["msg"];
      progressText.innerText = message;
      progressNumber.innerText = percent+"%";
      progressBar.style.width = percent+"%";
      if (percent < 100){
        window.setTimeout(updateProgressBar, 1000);
      } else {
        flag = false;
      }
      if (!flag) {
        hideProgressBar();
      }
    },
    error: function (result) {
      flag = false;
    }
  });
}
