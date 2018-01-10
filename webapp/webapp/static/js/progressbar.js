var progressGroup = document.getElementById("progress-group");
var progressText = document.getElementById("progress-text");
var progressNumber = document.getElementById("progress-number");
var progressBar = document.getElementById("progress-bar");
var flag = false;
var percent = 0;

function showProgressBar() {
  console.log("showProgressBar");
  flag = true;
  percent = 0;
}
function hideProgressBar() {
  console.log("hideProgressBar");
  flag = false;
  percent = 0;
}

function updateProgressBar(){
  $.ajax({
    type: "GET",
    url: "/progress",
    data: {
      progress: percent
    },
    success: function (result) {
      console.log("updateProgressBar success");
      console.log(result["msg"], result["percent"]);
      percent = result["percent"];
      progressText.innerText = result["msg"];
      progressNumber.innerText = percent+"%";
      progressBar.style.width = percent+"%";
      if (percent < 100 && flag) {
        window.setTimeout(updateProgressBar, 5000);
      }
      if (flag) {
        progressGroup.classList.remove("invisible");
      } else {
        progressGroup.classList.add("invisible");
      }
    },
    error: function (result) {
      console.log("updateProgressBar error");
    }
  });
}
