"""
UC-01: Generate and Share Brand-Safe Background Music.

Business rules encoded here (from SRS Appendix D, §10.2):
- REQ-4.2.1: Deduct tokens before dispatching generation.
- REQ-4.2.2: Block request if token balance is insufficient.
- REQ-4.3.7: Refund tokens when generation fails or times out.
"""

from django.db.models import F
from django.shortcuts import get_object_or_404

from ..models import Profile, Song, TokenRecord


class InsufficientTokensError(Exception):
    pass


class GenerateMusicController:
    """Controls the generate-and-share use case (UC-01)."""

    GENERATION_COST = 1

    @staticmethod
    def request_generation(user, title, genre="", mood="", occasion="", singer_style="", topic=""):
        """Validate tokens, create a GENERATING song record, and deduct the cost."""
        profile = get_object_or_404(Profile, user=user)
        if profile.token_balance < GenerateMusicController.GENERATION_COST:
            raise InsufficientTokensError(
                "Insufficient credits. Please contact the Administrator."
            )

        song = Song.objects.create(
            user=user,
            title=title,
            genre=genre,
            mood=mood,
            occasion=occasion,
            singer_style=singer_style,
            topic=topic,
            status=Song.SongStatus.GENERATING,
        )

        profile.token_balance -= GenerateMusicController.GENERATION_COST
        profile.save(update_fields=["token_balance"])
        TokenRecord.objects.create(
            user=user,
            amount=GenerateMusicController.GENERATION_COST,
            type=TokenRecord.TokenType.SPENT,
        )

        return song

    @staticmethod
    def mark_complete(song_id):
        """Mark a song COMPLETED after the background task succeeds."""
        song = get_object_or_404(Song, pk=song_id)
        song.status = Song.SongStatus.COMPLETED
        song.save(update_fields=["status"])
        return song

    @staticmethod
    def mark_failed(song_id):
        """Mark a song FAILED and refund the token cost to the owner."""
        song = get_object_or_404(Song, pk=song_id)
        song.status = Song.SongStatus.FAILED
        song.save(update_fields=["status"])

        Profile.objects.filter(user=song.user).update(
            token_balance=F("token_balance") + GenerateMusicController.GENERATION_COST
        )
        TokenRecord.objects.create(
            user=song.user,
            amount=GenerateMusicController.GENERATION_COST,
            type=TokenRecord.TokenType.EARNED,
        )

        return song

    @staticmethod
    def get_public_track(share_token):
        """Retrieve a publicly shared track by its share token (no login required)."""
        return get_object_or_404(Song, share_token=share_token, is_public=True)
