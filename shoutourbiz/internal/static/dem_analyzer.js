(function() {

// make profile pic and bio
function getProfilePicAndBio() {

	$.get(profile_pic_bio_url, function(data, status) {

		if(!data || data === 'None' || data == 'null') {
			$('#profile-details-sidebar').html('Cannot display profile preview...');
			return;
		}

		data = JSON.parse(data);

	    if(data.profile_url) {
	    	$('.user_img').attr('src', data.profile_url);
	    } else {
	    	$('.user_img').attr('src', anon_profile_path);
	    	return;
	    }

	    if(data.bio) {
	    	$('.profile-bio').html(data.bio);
	    } else {
	    	$('.profile-bio').html("Could not obtain user bio. Try viewing the profile directly on Instagram...");
	    	return;
	    }

	}).fail(function() {
		$('#profile-details-sidebar').html('Cannot display profile preview...');
	});
}

getProfilePicAndBio();

})();