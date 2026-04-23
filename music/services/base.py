"""
Strategy Pattern — abstract interface for AI music generation providers.

Any new provider (e.g. Udio, Stable Audio) only needs to:
  1. Subclass MusicGenerationStrategy
  2. Implement `name` and `generate()`
  3. Register in music/services/__init__.py
"""

from abc import ABC, abstractmethod


class MusicGenerationStrategy(ABC):
    """Abstract Strategy: declares the contract all providers must fulfil."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name (used in the UI and stored on Song)."""

    @abstractmethod
    def generate(self, song) -> str:
        """
        Submit song parameters to the AI API, poll until complete, and return
        the audio file URL.

        Raises:
            RuntimeError: API returned an error or unexpected response.
            TimeoutError: Generation did not complete within the allowed window.
            requests.RequestException: Network or HTTP failure.
        """
