"""
Strategy Pattern — factory / registry for music generation providers.

To add a new provider:
  1. Create a class in a new file (e.g. music/services/udio.py) that
     subclasses MusicGenerationStrategy and implements generate().
  2. Add one entry to _STRATEGIES below.

Active strategy selection (centralized):
  Set GENERATOR_STRATEGY in your .env to override the per-request provider:
    GENERATOR_STRATEGY=mock    → always use MockSongGeneratorStrategy (offline)
    GENERATOR_STRATEGY=suno    → always use SunoSongGeneratorStrategy
    GENERATOR_STRATEGY=mureka  → always use MurekaStrategy
    GENERATOR_STRATEGY=        → (empty / unset) use whatever the form submits
"""

from .base import MusicGenerationStrategy
from .mock import MockSongGeneratorStrategy
from .mureka import MurekaStrategy
from .suno import SunoStrategy

_STRATEGIES: dict[str, type[MusicGenerationStrategy]] = {
    "mock":   MockSongGeneratorStrategy,
    "mureka": MurekaStrategy,
    "suno":   SunoStrategy,
}

AVAILABLE_PROVIDERS = list(_STRATEGIES.keys())


def get_strategy(provider: str) -> MusicGenerationStrategy:
    """
    Return an instantiated strategy for the given provider name.

    If GENERATOR_STRATEGY is set in Django settings it overrides the requested
    provider, enabling global mock/test mode from a single env-var switch.
    """
    from django.conf import settings
    override = getattr(settings, 'GENERATOR_STRATEGY', '').lower().strip()
    resolved = override if override else provider.lower()
    cls = _STRATEGIES.get(resolved)
    if cls is None:
        raise ValueError(
            f"Unknown provider {resolved!r}. Available: {AVAILABLE_PROVIDERS}"
        )
    return cls()
