"""
Concrete Strategy — Mureka AI music generation.
Docs: https://platform.mureka.ai/docs/
"""

import logging

import requests
from django.conf import settings

from .base import MusicGenerationStrategy
from .utils import poll_until

logger = logging.getLogger("music")

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
            json={
                "prompt": prompt,
                "model": "auto",
                "lyrics": song.topic or "[instrumental]",
            },
            timeout=30,
        )
        resp.raise_for_status()
        task_id = resp.json()["id"]

        def fetch():
            r = requests.get(
                f"{_BASE_URL}/v1/song/query/{task_id}",
                headers={"Authorization": f"Bearer {settings.MUREKA_API_KEY}"},
                timeout=15,
            )
            r.raise_for_status()
            return r.json()

        def is_done(data):
            return data.get("state") == "complete"

        def has_failed(data):
            return data.get("state") == "failed"

        def get_result(data):
            songs = data.get("songs", [])
            return songs[0].get("mp3_url", "") if songs else ""

        return poll_until(
            fetch=fetch,
            is_done=is_done,
            has_failed=has_failed,
            get_result=get_result,
            task_id=task_id,
            timeout=_MAX_WAIT,
            interval=_POLL_INTERVAL,
        )

