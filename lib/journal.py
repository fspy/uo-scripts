"""Shared journal utilities for Legion scripts.

Provides helpers for waiting on journal messages with timeouts.

Note: API module is injected by Legion engine at runtime as a global.
Import is wrapped in try/except for type hints in editors.
"""

# pyright: basic
import time

# Try to import API for type hints, but don't fail if unavailable
try:
    import API
except (ImportError, NameError):
    pass  # API is injected at runtime by Legion engine


def wait_for_any(messages: list, timeout: float) -> bool:
    """
    Wait for any message from a list to appear in the journal.
    
    Polls the journal every 50ms until a message is found or timeout expires.
    
    Args:
        messages: List of strings to search for in journal
        timeout: Maximum seconds to wait
    
    Returns:
        True if any message found, False if timeout expired
    
    Example:
        if wait_for_any(["You chop", "That is too far"], timeout=2.0):
            # Message appeared
        else:
            # Timeout - no message found
    """
    deadline = time.time() + timeout
    while time.time() < deadline and not API.StopRequested:
        if API.InJournalAny(messages):
            return True
        API.Pause(0.05)
    return False
