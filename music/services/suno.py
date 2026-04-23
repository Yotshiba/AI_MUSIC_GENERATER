"""
Concrete Strategy — Suno AI music generation via sunoapi.org.
Docs: https://docs.sunoapi.org/
"""

import time

import requests
from django.conf import settings

from .base import MusicGenerationStrategy

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

        deadline = time.time() + _MAX_WAIT
        while time.time() < deadline:
            time.sleep(_POLL_INTERVAL)
            poll = requests.get(
                f"{base_url}/api/v1/generate/record-info",
                headers=headers,
                params={"taskId": task_id},
                timeout=15,
            )
            poll.raise_for_status()
            poll_body = poll.json()
            data      = poll_body.get("data") or {}
            status    = data.get("status", "")

            if status in ("SUCCESS", "FIRST_SUCCESS"):
                tracks = data.get("response", {}).get("data", [])
                if tracks:
                    # Prefer stream_audio_url (ready ~30 s) over audio_url (~2-3 min)
                    url = tracks[0].get("stream_audio_url") or tracks[0].get("audio_url")
                    if url:
                        return url
                raise RuntimeError("Suno returned SUCCESS but no audio URL found.")

            if status == "FAILED":
                raise RuntimeError(f"Suno generation failed: {data}")

        raise TimeoutError("Suno generation timed out after 5 minutes.")
