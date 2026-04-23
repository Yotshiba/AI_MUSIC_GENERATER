"""
Mureka AI music generation service.
Docs: https://platform.mureka.ai/docs/
"""

import time

import requests
from django.conf import settings

BASE_URL = "https://api.mureka.ai"
POLL_INTERVAL = 5   # seconds between status checks
MAX_WAIT = 300       # 5 minutes max


def _headers():
    return {"Authorization": f"Bearer {settings.MUREKA_API_KEY}"}


def generate(song):
    """
    Submit a generation request to Mureka and poll until complete.
    Returns the mp3_url string, or raises RuntimeError on failure/timeout.
    """
    prompt = " ".join(filter(None, [song.genre, song.mood, song.topic, song.occasion]))

    resp = requests.post(
        f"{BASE_URL}/v1/song/generate",
        headers=_headers(),
        json={"prompt": prompt, "model": "auto"},
        timeout=30,
    )
    resp.raise_for_status()
    task_id = resp.json()["id"]

    deadline = time.time() + MAX_WAIT
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        poll = requests.get(
            f"{BASE_URL}/v1/song/query/{task_id}",
            headers=_headers(),
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
