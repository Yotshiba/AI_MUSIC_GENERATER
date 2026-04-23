"""
Suno AI music generation service via sunoapi.org.
Docs: https://docs.sunoapi.org/
"""

import time

import requests
from django.conf import settings

BASE_URL = getattr(settings, "SUNO_BASE_URL", "https://api.sunoapi.org")
POLL_INTERVAL = 5   # seconds between status checks
MAX_WAIT = 300       # 5 minutes max


def _headers():
    return {"Authorization": f"Bearer {settings.SUNO_API_KEY}"}


def generate(song):
    """
    Submit a generation request to Suno and poll until complete.
    Returns the stream_audio_url string, or raises RuntimeError on failure/timeout.
    """
    prompt = " ".join(filter(None, [
        song.title, song.genre, song.mood, song.occasion, song.singer_style, song.topic,
    ]))

    resp = requests.post(
        f"{BASE_URL}/api/v1/generate",
        headers=_headers(),
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
    task_id = body["data"]["taskId"]

    deadline = time.time() + MAX_WAIT
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        poll = requests.get(
            f"{BASE_URL}/api/v1/generate/record-info",
            headers=_headers(),
            params={"taskId": task_id},
            timeout=15,
        )
        poll.raise_for_status()
        data = poll.json().get("data", {})
        status = data.get("status", "")

        if status in ("SUCCESS", "FIRST_SUCCESS"):
            tracks = data.get("response", {}).get("data", [])
            if tracks:
                # Prefer stream_audio_url (ready in ~30s) over audio_url (~2-3 min)
                url = tracks[0].get("stream_audio_url") or tracks[0].get("audio_url")
                if url:
                    return url
            raise RuntimeError("Suno returned SUCCESS but no audio URL found.")

        if status == "FAILED":
            raise RuntimeError(f"Suno generation failed: {data}")

    raise TimeoutError("Suno generation timed out after 5 minutes.")
