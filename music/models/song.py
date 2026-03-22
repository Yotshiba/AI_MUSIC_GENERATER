import uuid

from django.db import models

from .folder import Folder
from .user import User


class Song(models.Model):
    """Core domain entity representing a generated song."""

    class SongStatus(models.TextChoices):
        DRAFT = 'Draft', 'Draft'
        GENERATING = 'Generating', 'Generating'
        COMPLETED = 'Completed', 'Completed'
        FAILED = 'Failed', 'Failed'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='songs')
    folder = models.ForeignKey(
        Folder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='songs',
    )

    title = models.CharField(max_length=200)
    genre = models.CharField(max_length=100, blank=True)
    mood = models.CharField(max_length=100, blank=True)
    occasion = models.CharField(max_length=100, blank=True)
    singer_style = models.CharField(max_length=100, blank=True)
    topic = models.CharField(max_length=200, blank=True)
    duration = models.PositiveIntegerField(help_text='Duration in seconds', default=0)
    status = models.CharField(
        max_length=12,
        choices=SongStatus.choices,
        default=SongStatus.DRAFT,
    )
    is_public = models.BooleanField(default=False)
    share_token = models.UUIDField(default=uuid.uuid4, unique=True)

    def __str__(self):
        return self.title
