"""
Strategy A (Mock) — offline, deterministic song generation.

Used for local development and testing without network access.
Activate by setting GENERATOR_STRATEGY=mock in your .env file.
"""

import time

from .base import MusicGenerationStrategy

# A freely-available, royalty-free sample track used as a stand-in.
_MOCK_AUDIO_URL = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
_MOCK_DELAY_SECONDS = 2  # simulate brief processing time


class MockSongGeneratorStrategy(MusicGenerationStrategy):
    """
    Concrete Mock Strategy: returns a fixed placeholder audio URL immediately.
    No network calls, no API key required — safe for offline development and CI.
    """

    @property
    def name(self) -> str:
        return "Mock"

    def generate(self, song) -> str:
        """
        Simulate generation by sleeping briefly, then return a fixed audio URL.
        Output is fully deterministic regardless of song parameters.
        """
        time.sleep(_MOCK_DELAY_SECONDS)
        return _MOCK_AUDIO_URL
