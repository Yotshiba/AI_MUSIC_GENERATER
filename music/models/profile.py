from django.db import models

from .user import User


class Profile(models.Model):
    """One-to-one profile for a User, holding token balance."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    token_balance = models.IntegerField(default=0)

    def __str__(self):
        return f"Profile of {self.user.name}"
