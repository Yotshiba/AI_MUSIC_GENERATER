"""
Music API service selector.
Set MUSIC_API_PROVIDER=mureka or suno in your .env file.
"""

from django.conf import settings


def generate(song):
    provider = getattr(settings, "MUSIC_API_PROVIDER", "mureka").lower()
    if provider == "suno":
        from .suno import generate as _generate
    else:
        from .mureka import generate as _generate
    return _generate(song)
