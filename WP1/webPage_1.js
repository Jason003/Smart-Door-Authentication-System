$(document).ready(function() {

	var faceId = getUrlVars()["faceId"];

	function getUrlVars() {
	    var vars = {};
	    var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m,key,value) {
	        vars[key] = value;
	    });
	    return vars;
	}

	$("#decline").click(function() {
		var apigClient = apigClientFactory.newClient();
		var params = {};
		var body = {
			"faceId": faceId,
			"name": "N/A",
			"phoneNumber": "N/A"
		};
		var additionalParams = {};
		apigClient.authenticatePost(params, body, additionalParams).then(
			function (result) {
				console.log(result.data.message);
				var reg = new RegExp('"',"g");
				respond = result.data.message.replace(reg, "");

				$(".respond_text").append(respond);
				$(".initial").css('visibility', 'hidden');
				$(".form").css('visibility', 'hidden');
				$(".response").css('visibility', 'visible');
				
			}).catch(function (result) {
			});
	});

	$("#accept").click(function() {
		$(".initial").css('visibility', 'hidden');
		$(".response").css('visibility', 'hidden');
		$(".form").css('visibility', 'visible');
	});

	$("#submit").click(function() {
		name = $(".name").val();
		phone = $(".phone").val();
		var apigClient = apigClientFactory.newClient();
		var params = {};
		var body = {
			"faceId": faceId,
			"name": name,
			"phoneNumber": phone
		};
		var additionalParams = {};
		apigClient.authenticatePost(params, body, additionalParams).then(
			function (result) {
				console.log(result.data.message);
				var reg = new RegExp('"',"g");
				respond = result.data.message.replace(reg, "");

				$(".respond_text").append(respond);
				$(".initial").css('visibility', 'hidden');
				$(".form").css('visibility', 'hidden');
				$(".response").css('visibility', 'visible');
				
			}).catch(function (result) {
			});
	});
});