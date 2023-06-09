$(document).ready(function () {
  $(".message a").click(function () {
    if($(".register-form").css("display") == 'none') {
      $(".login-form").hide("fast");
      $(".register-form").show("slow");
    } else {
      $(".register-form").hide("fast");
      $(".login-form").show("slow");
    }
  });
});
function validate() {
  var p1 = $(".register-form #password").val();
  var p2 = $(".register-form #rpassword").val();
  var pswlen = p1.length;
  if (pswlen < 3) {
    alert("minmum 4 characters needed");
    return false;
  } else {
    return p1 == p2;
  }
}
function send() {
  if (
    $("#num_lines_per_evaluation").val() > 0 &&
    $("#dataset").val() &&
    $("#control").val()
  ) {
    $("#btn_spinner").show();
    $("#btn_send").hide();
    $("#btn_spinner").click();
  } else {
    $("#btn_spinner").click();
  }
}
function copy() {
  var copyText = document.getElementById("copy_url");
  copyText.select();
  copyText.setSelectionRange(0, 99999);
  navigator.clipboard.writeText(copyText.value);
}
