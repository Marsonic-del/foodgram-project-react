from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    password = models.CharField(("password"), max_length=150)
    is_subscribed = models.BooleanField(default=False)
    email = models.EmailField('email address', max_length=254, unique=True, blank=False, null=False)
    first_name = models.CharField('first name', max_length=150, blank=False, null=False)
    last_name = models.CharField('last name', max_length=150, blank=False, null=False)

    class Meta(AbstractUser.Meta):
        swappable = "AUTH_USER_MODEL"
