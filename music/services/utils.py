"""
Shared utilities for music generation services.
"""

import logging
import time
from typing import Any, Callable

logger = logging.getLogger("music")


def poll_until(
    fetch: Callable[[], Any],
    is_done: Callable[[Any], bool],
    has_failed: Callable[[Any], bool],
    get_result: Callable[[Any], str],
    task_id: str = "",
    timeout: int = 1200,
    interval: int = 5,
) -> str:
    """
    Poll fetch() every interval seconds until is_done() or has_failed() returns True.

    Args:
        fetch:      Callable that performs the status GET and returns parsed response data.
        is_done:    Returns True when generation has completed successfully.
        has_failed: Returns True when generation has permanently failed.
        get_result: Extracts the audio URL string from a successful response.
        task_id:    Used only for log messages.
        timeout:    Maximum seconds to wait before raising TimeoutError.
        interval:   Seconds to sleep between polls.

    Returns:
        Audio URL string on success.

    Raises:
        RuntimeError: Provider reported failure or successful response had no URL.
        TimeoutError: Generation did not complete within timeout seconds.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(interval)
        data = fetch()
        logger.debug("poll_until taskId=%s data=%s", task_id, data)

        if is_done(data):
            url = get_result(data)
            if url:
                return url
            raise RuntimeError(f"Provider returned success but no audio URL (taskId={task_id}).")

        if has_failed(data):
            logger.error("Provider reported failure: taskId=%s data=%s", task_id, data)
            raise RuntimeError(f"Generation failed (taskId={task_id}): {data}")

    raise TimeoutError(f"Generation timed out after {timeout}s (taskId={task_id}).")
