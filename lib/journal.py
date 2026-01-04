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


def find_entry(pattern, timeout=5.0, seconds_back=5):
    """
    Wait for and return a journal entry matching a pattern.
    
    Polls the journal every 50ms until a matching entry is found or timeout expires.
    
    Args:
        pattern: String or regex pattern to search for (prefix with $ for regex)
        timeout: Maximum seconds to wait for the entry
        seconds_back: How many seconds back to search in journal history
    
    Returns:
        Journal entry object with .Text, .Name, .Hue attributes, or None if timeout
    
    Example:
        entry = find_entry("offer may be available", timeout=2.0)
        if entry:
            print(f"{entry.Name} said: {entry.Text}")
        else:
            print("No matching entry found")
    """
    deadline = time.time() + timeout
    while time.time() < deadline and not API.StopRequested:
        entries = API.GetJournalEntries(seconds_back, pattern)
        if entries:
            # Return the most recent matching entry
            return entries[-1]
        API.Pause(0.05)
    return None
