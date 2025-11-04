from django.contrib.auth.backends import BaseBackend
from .models import User
from django.db.models import Q

class CustomAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(
                Q(email__iexact=username) | 
                Q(phone_number__iexact=username) | 
                Q(cccd__iexact=username)
            )
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            return User.objects.filter(email__iexact=username).first()

        if user.check_password(password) and user.is_active:
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None