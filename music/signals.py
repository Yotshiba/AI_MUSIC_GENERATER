"""
Django signals for the music app.

Creator pattern: when a music.User is created, automatically provision
a Profile (token balance) and a Library (song container) for them.
This removes the creation responsibility from views.py.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Library, Profile, User


@receiver(post_save, sender=User)
def provision_user_resources(sender, instance, created, **kwargs):
    """On first save of a new User, create their Profile and Library."""
    if created:
        Profile.objects.get_or_create(
            user=instance,
            defaults={'token_balance': 10},
        )
        Library.objects.get_or_create(user=instance)
