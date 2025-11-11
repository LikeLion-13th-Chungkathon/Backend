from django.db import models
from django.contrib.auth.base_user import AbstractUser


class User(AbstractUser):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)