"""
Concrete Strategy — Suno AI music generation via sunoapi.org.
Docs: https://docs.sunoapi.org/
"""

import logging

import requests
from django.conf import settings

from .base import MusicGenerationStrategy
from .utils import poll_until

logger = logging.getLogger("music")

_POLL_INTERVAL = 5    # seconds between status checks
_MAX_WAIT      = 300  # 5 minutes


class SunoStrategy(MusicGenerationStrategy):
    """Concrete Strategy B: generates music via the Suno unofficial API."""

    @property
    def name(self) -> str:
        return "Suno"

    def generate(self, song) -> str:
        base_url = getattr(settings, "SUNO_BASE_URL", "https://api.sunoapi.org")
        headers  = {"Authorization": f"Bearer {settings.SUNO_API_KEY}"}

        prompt = " ".join(filter(None, [
            song.title, song.genre, song.mood, song.occasion, song.singer_style, song.topic,
        ]))

        resp = requests.post(
            f"{base_url}/api/v1/generate",
            headers=headers,
            json={
                "prompt": prompt[:500],
                "customMode": False,
                "instrumental": not bool(song.singer_style),
                "model": "V4_5ALL",
                "callBackUrl": "https://example.com/callback",
            },
            timeout=30,
        )
        resp.raise_for_status()
        body = resp.json()
        if not isinstance(body.get("data"), dict) or not body["data"].get("taskId"):
            raise RuntimeError(
                f"Suno API rejected the request: {body.get('msg') or body}"
            )
        task_id = body["data"]["taskId"]

        def fetch():
            r = requests.get(
                f"{base_url}/api/v1/generate/record-info",
                headers=headers,
                params={"taskId": task_id},
                timeout=15,
            )
            r.raise_for_status()
            return r.json().get("data") or {}

        def is_done(data):
            return data.get("status") in ("SUCCESS", "FIRST_SUCCESS")

        def has_failed(data):
            return data.get("status") == "FAILED"

        def get_result(data):
            tracks = data.get("response", {}).get("sunoData", [])
            if tracks:
                # Prefer streamAudioUrl (ready ~30 s) over audioUrl (~2-3 min)
                return tracks[0].get("streamAudioUrl") or tracks[0].get("audioUrl") or ""
            return ""

        return poll_until(
            fetch=fetch,
            is_done=is_done,
            has_failed=has_failed,
            get_result=get_result,
            task_id=task_id,
            timeout=_MAX_WAIT,
            interval=_POLL_INTERVAL,
        )

