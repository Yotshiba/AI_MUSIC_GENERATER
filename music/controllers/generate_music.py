"""
UC-01: Generate and Share Brand-Safe Background Music.

Business rules encoded here (from SRS Appendix D, §10.2):
- REQ-4.2.1: Deduct tokens before dispatching generation.
- REQ-4.2.2: Block request if token balance is insufficient.
- REQ-4.3.7: Refund tokens when generation fails or times out.
"""

import logging

from django.db import transaction
from django.shortcuts import get_object_or_404

from ..models import GenerationLog, InsufficientTokensError, Profile, Song
from ..profanity import contains_profanity

logger = logging.getLogger("music")


class ProfanityError(Exception):
    pass


class GenerateMusicController:
    """Controls the generate-and-share use case (UC-01)."""

    GENERATION_COST = 1

    @staticmethod
    @transaction.atomic
    def request_generation(user, title, genre="", mood="", occasion="", singer_style="", topic="", provider=""):
        """Validate input, deduct tokens, create a GENERATING song record."""
        # Controller GRASP: validation is part of this use case, not the view.
        if any(contains_profanity(f) for f in [title, mood, topic, genre]):
            raise ProfanityError(
                "Your input contains inappropriate language. "
                "Please revise to comply with platform safety guidelines."
            )

        profile = get_object_or_404(Profile, user=user)

        # Information Expert: Profile knows whether it can afford the cost.
        profile.deduct(GenerateMusicController.GENERATION_COST)

        song = Song.objects.create(
            user=user,
            title=title,
            genre=genre,
            mood=mood,
            occasion=occasion,
            singer_style=singer_style,
            topic=topic,
            provider=provider,
            status=Song.SongStatus.QUEUED,
        )

        GenerationLog.objects.create(
            user=user,
            song=song,
            title=title,
            genre=genre,
            mood=mood,
            occasion=occasion,
            singer_style=singer_style,
            topic=topic,
            provider=provider,
            status=GenerationLog.Status.PENDING,
        )

        return song

    @staticmethod
    @transaction.atomic
    def mark_complete(song_id, file_url=""):
        """Mark a song COMPLETED, store the audio URL, and finalise the audit log."""
        song = get_object_or_404(Song, pk=song_id)
        # Information Expert: Song owns its own state transition.
        song.mark_complete(file_url)
        GenerationLog.objects.filter(song_id=song_id).update(status=GenerationLog.Status.SUCCESS)
        return song

    @staticmethod
    @transaction.atomic
    def mark_failed(song_id):
        """Mark a song FAILED and refund the token cost to the owner."""
        song = get_object_or_404(Song, pk=song_id)
        # Information Expert: Song owns its own state transition.
        song.mark_failed()

        GenerationLog.objects.filter(song_id=song_id).update(status=GenerationLog.Status.FAILED)

        # Information Expert: Profile owns the refund logic.
        profile = get_object_or_404(Profile, user=song.user)
        profile.refund(GenerateMusicController.GENERATION_COST)

        return song

