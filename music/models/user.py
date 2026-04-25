from django.db import models


class User(models.Model):
    """Domain entity representing a user of the AI Music Generator."""

    class UserRole(models.TextChoices):
        CREATOR = 'Creator', 'Creator'
        ADMIN = 'Admin', 'Admin'

    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.CREATOR,
    )

    def __str__(self):
        return self.name

    @classmethod
    def from_auth_user(cls, auth_user):
        """Creator: get or create a music.User from a Django auth.User.
        Profile and Library are provisioned automatically via post_save signal.
        """
        music_user, _ = cls.objects.get_or_create(
            email=auth_user.email,
            defaults={
                'name': auth_user.get_full_name() or auth_user.username or auth_user.email,
                'role': cls.UserRole.CREATOR,
            },
        )
        return music_user
