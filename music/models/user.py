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
