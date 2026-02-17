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

from typing import List, cast

from _lib.persistence import load_int, save_int

NOTORIETY_FRIENDLY = cast(
    List[API.Notoriety], [API.Notoriety.Ally, API.Notoriety.Innocent]
)
NOTORIETY_ENEMY = cast(
    List[API.Notoriety],
    [
        API.Notoriety.Enemy,
        API.Notoriety.Gray,
        API.Notoriety.Murderer,
        API.Notoriety.Criminal,
    ],
)


class Hue:
    Black = 1
    Blue = 2122
    Cyan = 90
    Gray = 1000
    Green = 63
    Magenta = 128
    Orange = 2736
    Red = 33
    Yellow = 253
    White = 1150


def p(msg, hue=Hue.White):
    API.SysMsg(str(msg), hue)


def h(msg, serial=API.Player, hue=Hue.White):
    API.HeadMsg(str(msg), serial, hue)


def toggle_mount():
    if API.Player.Mount:
        API.Dismount()
    else:
        mount = load_int("mount")
        if not mount:
            h("Target Mount", hue=Hue.Orange)
            target = API.RequestTarget()
            if not target:
                h("Invalid Target", hue=Hue.Red)
                return
            save_int("mount", target)
            mount = target

        API.Mount(mount)


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
