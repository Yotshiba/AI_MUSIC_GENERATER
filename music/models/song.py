import uuid

from django.db import models

from .folder import Folder
from .user import User


class Song(models.Model):
    """Core domain entity representing a generated song."""

    class SongStatus(models.TextChoices):
        DRAFT = 'Draft', 'Draft'
        QUEUED = 'Queued', 'Queued'
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
    provider = models.CharField(max_length=20, blank=True)
    file_url = models.URLField(blank=True)
    is_public = models.BooleanField(default=False)
    share_token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    # ── Information Expert: status transitions owned by Song ──────────────

    def mark_queued(self) -> None:
        """Transition to QUEUED (task submitted, worker not yet started)."""
        self.status = self.SongStatus.QUEUED
        self.save(update_fields=["status"])

    def mark_generating(self) -> None:
        """Transition to GENERATING (worker has picked up the task)."""
        self.status = self.SongStatus.GENERATING
        self.save(update_fields=["status"])

    def mark_complete(self, file_url: str) -> None:
        """Transition to COMPLETED and store the audio URL."""
        self.status = self.SongStatus.COMPLETED
        self.file_url = file_url
        self.save(update_fields=["status", "file_url"])

    def mark_failed(self) -> None:
        """Transition to FAILED."""
        self.status = self.SongStatus.FAILED
        self.save(update_fields=["status"])

    def toggle_privacy(self) -> None:
        """Flip the public/private flag."""
        self.is_public = not self.is_public
        self.save(update_fields=["is_public"])
