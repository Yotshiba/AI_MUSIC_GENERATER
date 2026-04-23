"""
Strategy Pattern — factory / registry for music generation providers.

To add a new provider:
  1. Create a class in a new file (e.g. music/services/udio.py) that
     subclasses MusicGenerationStrategy and implements generate().
  2. Add one entry to _STRATEGIES below.
"""

from .base import MusicGenerationStrategy
from .mureka import MurekaStrategy
from .suno import SunoStrategy

_STRATEGIES: dict[str, type[MusicGenerationStrategy]] = {
    "mureka": MurekaStrategy,
    "suno":   SunoStrategy,
}

AVAILABLE_PROVIDERS = list(_STRATEGIES.keys())


def get_strategy(provider: str) -> MusicGenerationStrategy:
    """Return an instantiated strategy for the given provider name."""
    cls = _STRATEGIES.get(provider.lower())
    if cls is None:
        raise ValueError(
            f"Unknown provider {provider!r}. Available: {AVAILABLE_PROVIDERS}"
        )
    return cls()
