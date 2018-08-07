function formatNiches(text) {
	var nicheList, resultList, resultString;
	resultString = text.replace(/\s*,\s*/g, ', ');
	return resultString;
}

$(document).ready(function(){
	$('.niches-input').on('input', function(event) {
		var elem, resText;
		elem = $(this);
		resText = formatNiches(elem.val());
		elem.val(resText);
	});
});