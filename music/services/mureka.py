"""
Concrete Strategy — Mureka AI music generation.
Docs: https://platform.mureka.ai/docs/
"""

import time

import requests
from django.conf import settings

from .base import MusicGenerationStrategy

_BASE_URL      = "https://api.mureka.ai"
_POLL_INTERVAL = 5    # seconds between status checks
_MAX_WAIT      = 300  # 5 minutes


class MurekaStrategy(MusicGenerationStrategy):
    """Concrete Strategy A: generates music via the Mureka official API."""

    @property
    def name(self) -> str:
        return "Mureka"

    def generate(self, song) -> str:
        prompt = " ".join(filter(None, [song.genre, song.mood, song.topic, song.occasion]))

        resp = requests.post(
            f"{_BASE_URL}/v1/song/generate",
            headers={"Authorization": f"Bearer {settings.MUREKA_API_KEY}"},
            json={"prompt": prompt, "model": "auto"},
            timeout=30,
        )
        resp.raise_for_status()
        task_id = resp.json()["id"]

        deadline = time.time() + _MAX_WAIT
        while time.time() < deadline:
            time.sleep(_POLL_INTERVAL)
            poll = requests.get(
                f"{_BASE_URL}/v1/song/query/{task_id}",
                headers={"Authorization": f"Bearer {settings.MUREKA_API_KEY}"},
                timeout=15,
            )
            poll.raise_for_status()
            data = poll.json()
            state = data.get("state", "")

            if state == "complete":
                songs = data.get("songs", [])
                if songs and songs[0].get("mp3_url"):
                    return songs[0]["mp3_url"]
                raise RuntimeError("Mureka returned complete state but no mp3_url.")

            if state == "failed":
                raise RuntimeError(f"Mureka generation failed: {data}")

        raise TimeoutError("Mureka generation timed out after 5 minutes.")
