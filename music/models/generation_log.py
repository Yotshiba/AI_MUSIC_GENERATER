"""
Audit log for every music generation request (REQ-5.2.2 Thai law compliance).
Captures all user-submitted inputs and final outcome for each generation attempt.
"""

from django.db import models

from .song import Song
from .user import User


class GenerationLog(models.Model):
    class Status(models.TextChoices):
        SUCCESS = 'Success', 'Success'
        FAILED = 'Failed', 'Failed'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generation_logs')
    song = models.ForeignKey(Song, on_delete=models.SET_NULL, null=True, blank=True, related_name='generation_logs')
    title = models.CharField(max_length=200)
    genre = models.CharField(max_length=100, blank=True)
    mood = models.CharField(max_length=100, blank=True)
    occasion = models.CharField(max_length=100, blank=True)
    singer_style = models.CharField(max_length=100, blank=True)
    topic = models.CharField(max_length=200, blank=True)
    provider = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.SUCCESS)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.user} — {self.title} ({self.status})'
