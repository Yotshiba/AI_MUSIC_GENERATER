from django.db import models

from .user import User


class Library(models.Model):
    """Each User has exactly one Library that organises their songs into folders."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='library')

    class Meta:
        verbose_name_plural = 'libraries'

    def __str__(self):
        return f"Library of {self.user.name}"
