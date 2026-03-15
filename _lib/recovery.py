"""Shared recovery and shutdown utilities for Legion scripts.

Provides helpers for detecting stuck states and gracefully shutting down
scripts when unrecoverable errors occur.

Note: API module is injected by Legion engine at runtime as a global.
Import is wrapped in try/except for type hints in editors.
"""

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import API


def is_stuck(timeout=10):
    """
    Check if player hasn't moved in the last N seconds.

    Uses a closure to track position between calls without global state.

    Args:
        timeout: Seconds of no movement before considering stuck (default 10)

    Returns:
        True if stuck (no movement detected), False otherwise

    Example:
        if is_stuck():
            API.SysMsg("Stuck - attempting recovery", 32)
    """
    if not hasattr(is_stuck, "last_pos"):
        is_stuck.last_pos = (API.Player.X, API.Player.Y)
        is_stuck.last_check = time.time()
        return False

    now = time.time()
    if now - is_stuck.last_check > timeout:
        current_pos = (API.Player.X, API.Player.Y)
        if current_pos == is_stuck.last_pos:
            is_stuck.last_check = now
            is_stuck.last_pos = current_pos
            return True
        is_stuck.last_check = now
        is_stuck.last_pos = current_pos
    return False


def shutdown_cleanly(home_serial=None, runebook_serial=None, max_retries=3):
    """
    Attempt to recall home before stopping script.

    Tries to recall to home if a target serial is provided, then stops
    the script cleanly. If recall fails after retries, still stops.

    Args:
        home_serial: Optional serial of home rune or runebook
        runebook_serial: Optional serial of runebook (alternative to home_serial)
        max_retries: Number of recall attempts (default 3)

    Returns:
        True if recall succeeded, False if failed

    Example:
        if consecutive_failures >= 5:
            if shutdown_cleanly(home_rune.Serial):
                return
            stop_script("Cannot recover - stopping")
    """
    from _lib.runebook import recall_with_retry

    target = home_serial or runebook_serial
    if target:
        API.SysMsg("Attempting to recall home before shutdown...", 946)
        if recall_with_retry(target, max_retries=max_retries):
            API.SysMsg("Made it home safely", 62)
            return True
        else:
            API.SysMsg("Failed to recall home - stopping anyway", 32)
            return False

    API.SysMsg("No home target set - stopping script", 946)
    return False
