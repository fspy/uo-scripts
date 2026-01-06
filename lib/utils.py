"""Shared utility functions for Legion scripts.

Provides common helpers used across multiple scripts including distance
calculations, item counting, script control, and more.

Note: API module is injected by Legion engine at runtime as a global.
Import is wrapped in try/except for type hints in editors.
"""

# pyright: basic
# Try to import API for type hints, but don't fail if unavailable
try:
    import API
except (ImportError, NameError):
    pass  # API is injected at runtime by Legion engine


def chebyshev_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    """
    Calculate Chebyshev distance (max of x/y deltas).

    Also known as "chessboard distance" or "maximum metric".
    This is how UO calculates distance for most purposes.

    Args:
        x1, y1: First point coordinates
        x2, y2: Second point coordinates

    Returns:
        Maximum absolute difference between x coordinates and y coordinates
    """
    return max(abs(x1 - x2), abs(y1 - y2))


def count_items(graphic: int, container) -> int:
    """
    Count total amount of items with graphic in container.

    Sums the Amount property of all matching items. For stackable items,
    this gives the total stack count. For non-stackable items, it counts
    the number of items.

    Args:
        graphic: Item graphic ID (type)
        container: Container object or serial to search in

    Returns:
        Total count of items (sum of Amount properties)
    """
    items = API.FindTypeAll(graphic, container) or []
    return sum(getattr(it, "Amount", 0) or 0 for it in items)


def find_any_type(types: list, container, min_amount: int = 0):
    """
    Find first item matching any type in the list.

    Searches for items in order and returns the first match found.

    Args:
        types: List of graphic IDs to search for
        container: Container object or serial to search in
        min_amount: Minimum stack amount required (default 0)

    Returns:
        First matching item object, or None if no match found
    """
    for item_type in types:
        item = API.FindType(item_type, container, minamount=min_amount)
        if item:
            return item
    return None


def stop_script(msg: str, hue: int = 32) -> None:
    """
    Stop script with a system message.

    Displays message and stops script execution. Useful for error handling
    and graceful script termination.

    Args:
        msg: Message to display to player
        hue: Message color (default 32 = red for errors)
    """
    API.SysMsg(msg, hue)
    API.Stop()


def dismount_if_mounted(delay: float = 0.5) -> None:
    """
    Dismount if player is currently mounted.

    Some actions (like mining) require being on foot. This helper checks
    if mounted and dismounts if necessary.

    Args:
        delay: Seconds to pause after dismounting (default 0.5)
    """
    if API.Player and API.Player.Mount:
        API.Dismount()
        API.Pause(delay)


def use_item_on_target(item_serial, target_serial, timeout=2.0, delay=0.5):
    """
    Standard use-object-then-target sequence.

    Common pattern for tools that need a target (axes on trees, pickaxes on ore, etc.)
    Handles the use-wait-target-pause flow that appears throughout the codebase.

    Args:
        item_serial: Serial of item to use
        target_serial: Serial of target
        timeout: Seconds to wait for target cursor
        delay: Pause after targeting

    Returns:
        True if targeting succeeded, False if no target cursor appeared

    Example:
        if use_item_on_target(pickaxe.Serial, ore_vein.Serial):
            API.SysMsg("Mining...")
    """
    API.UseObject(item_serial)
    if API.WaitForTarget(timeout=timeout):
        API.Target(target_serial)  # type: ignore
        API.Pause(delay)
        return True
    return False


def format_time_remaining(seconds):
    """
    Format seconds as human-readable time.

    Converts a time duration in seconds to a compact, readable format.
    Useful for displaying cooldowns, timers, and ETA information.

    Args:
        seconds: Seconds remaining (can be float or int)

    Returns:
        Formatted time string like "5h 59m", "45m", or "READY!"

    Example:
        format_time_remaining(3661)   # Returns "1h 1m"
        format_time_remaining(120)     # Returns "2m"
        format_time_remaining(-5)      # Returns "READY!"
    """
    if seconds <= 0:
        return "READY!"

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)

    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"
