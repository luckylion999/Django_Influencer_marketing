def is_assistant(user):
	"""
	Return true if user is an assistant, False otherwise
	"""

	if user.groups.filter(name='assistant').exists():
		return True
	return False

def is_superuser(user):
	"""
	Return true if user is superuser (admin)
	"""

	return user.is_superuser

def validate_perms(user):
	"""
	Return True if user is authenticated (logged in)
	"""

	return user.is_authenticated()

def is_internal_user(user):
    if user:
        if user.is_authenticated():
            return _is_superuser(request.user) or is_assistant(request.user)
    return False
