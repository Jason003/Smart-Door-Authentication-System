$(document).ready(function() {
	$("#submit").click(function() {
		sendMessage();		
	});

	function sendMessage() {
		msg = $(".OTP_input").val();
		if ($.trim(msg) == '') {
			return false;
		}

		console.log(msg);

		var apigClient = apigClientFactory.newClient();
		var params = {};
		var body = {
			"OTP": msg
		};
		var additionalParams = {};
		apigClient.validatePost(params, body, additionalParams).then(
			function (result) {
				console.log(result.data.message);
				var reg = new RegExp('"',"g");
				respond = result.data.message.replace(reg, "");

				$('body').css('background-image', 'url("open.png")');
				$(".initial").css('visibility', 'hidden');
				$(".respond_text").append(respond);
				$(".response").addClass('response_container');
				$(".response").css('visibility', 'visible');
				
			}).catch(function (result) {
			});
	}
});