from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator

class LoginRequiredMixin(object):

	@method_decorator(login_required)
	def dispatch(self, request, *args, **kwargs):
		return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)

class SuperUserMixin(object):

	@permission_required('is_superuser')
	def dispatch(self, request, *args, **kwargs):
		return super(SuperUserMixin, self).dispatch(request, *args, **kwargs)
