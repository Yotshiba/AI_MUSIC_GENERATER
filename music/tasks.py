"""
Background tasks executed by django-q2 workers (REQ-4.3.2).

Start the worker with: python manage.py qcluster
"""

from .controllers import GenerateMusicController
from .services import get_strategy


def generate_music_task(song_id: int, provider: str) -> None:
    """
    Calls the external music API and updates the Song to COMPLETED or FAILED.
    Runs in a worker process — never blocks the HTTP request cycle.
    Token refund on failure is handled by mark_failed().
    """
    try:
        from .models import Song
        song = Song.objects.get(pk=song_id)
        strategy = get_strategy(provider)
        file_url = strategy.generate(song)
        GenerateMusicController.mark_complete(song_id, file_url=file_url)
    except Exception:
        GenerateMusicController.mark_failed(song_id)
