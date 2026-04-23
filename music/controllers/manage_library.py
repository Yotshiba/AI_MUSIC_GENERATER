"""
UC-02: Manage Personal Library & Playback.

Business rules encoded here (from SRS Appendix D, §10.3):
- Ownership: users can only delete or modify tracks they created.
- Privacy Default: tracks are private until explicitly toggled public.
"""

from django.shortcuts import get_object_or_404

from ..models import Song


class ManageLibraryController:
    """Controls the personal library management use case (UC-02)."""

    @staticmethod
    def list_tracks(user):
        """Return all songs owned by the user, newest first."""
        return Song.objects.filter(user=user).order_by("-pk")

    @staticmethod
    def delete_track(song_id, user):
        """Delete a track, enforcing that the requesting user is the owner."""
        song = get_object_or_404(Song, pk=song_id, user=user)
        song.delete()

    @staticmethod
    def toggle_privacy(song_id, user):
        """Toggle a track's public/private status; returns the updated song."""
        song = get_object_or_404(Song, pk=song_id, user=user)
        song.is_public = not song.is_public
        song.save(update_fields=["is_public"])
        return song

    @staticmethod
    def get_public_track(share_token):
        """Retrieve a public track by share token (accessible to Public Listeners)."""
        return get_object_or_404(Song, share_token=share_token, is_public=True)
