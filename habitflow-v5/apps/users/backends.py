from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailOrUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        if username is None:
            return None
        field = "email__iexact" if "@" in username else "username"
        user = User.objects.filter(**{field: username}).first()
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
