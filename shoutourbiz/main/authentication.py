from .models import AuthUser

class EmailAuthBackend(object):

    def authenticate(self, username=None, password=None):
        try:
            user = AuthUser.objects.get(email=username)
            if user.check_password(password):
                return user
            return None
        except AuthUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return AuthUser.objects.get(id=user_id)
        except AuthUser.DoesNotExist:
            return None