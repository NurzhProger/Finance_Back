from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone


@receiver(user_logged_in)
def after_user_logged_in(sender, request, user, **kwargs):
    ф = 1