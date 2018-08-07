from main.models import UnlockedUsers

def is_assistant(user):
	"""
	Check whether the current user is an assistant.
	"""
	if user.groups.filter(name='assistant').exists():
		return True
	return False

def is_external_user(user):
	"""
	Check whether the current user is an external user, meaning that
	they are not an assistant and they are not a superuser.
	"""
	if not (user.is_authenticated() and user.is_superuser or is_assistant(user)):
		return True
	return False

def is_unlocked_by_buyer(user, influencer, network):
	"""
	Check if the user has already unlocked the influencer.
	"""
	if not user.is_authenticated():
		return False
	if UnlockedUsers.objects.filter(buyer_id=user.id, user_id=influencer.id, network=network).exists():
		return True