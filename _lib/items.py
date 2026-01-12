"""Shared item moving utilities for Legion scripts.

Note: API module is injected by Legion engine at runtime as a global.
Import is wrapped in try/except for type hints in editors.
"""

# pyright: basic
# Try to import API for type hints, but don't fail if unavailable
try:
    import API
except (ImportError, NameError):
    pass  # API is injected at runtime by Legion engine


def move_item_robust(serial, dest, amount, max_retries=5):
    """
    Move item with retry logic for 'you must wait' messages.
    Uses adaptive delays starting at 0.6s and increasing by 0.1s per retry, capped at 1.5s.
    Returns True if move succeeded (or no error detected), False if failed after retries.
    """
    base_delay = 0.6
    max_delay = 1.5
    delay_increment = 0.1

    for attempt in range(max_retries):
        API.ClearJournal()
        API.MoveItem(serial, dest, amt=amount)

        # Incremental delay: 0.6s, 0.7s, 0.8s, ..., capped at 1.5s
        current_delay = min(base_delay + (attempt * delay_increment), max_delay)
        API.Pause(current_delay)

        # Check for "you must wait"
        if API.InJournalAny(["you must wait"]):
            if attempt < max_retries - 1:
                API.HeadMsg("Waiting...", API.Player.Serial, 946)
                continue
            else:
                # Final attempt failed
                return False

        # Success or no "must wait" message - move on
        return True

    return False


def drop_items_to_container(container_serial, item_types, source=None):
    """
    Move all items of specified types to a container.

    Args:
        container_serial: Destination container serial
        item_types: List of item graphic IDs to move
        source: Source container (defaults to API.Backpack)

    Returns: count of item stacks dropped
    """
    if source is None:
        source = API.Backpack

    dropped_count = 0

    for item_type in item_types:
        items = API.FindTypeAll(item_type, source) or []
        for item in items:
            if API.StopRequested:
                break
            amount = getattr(item, "Amount", 0) or 0
            if amount > 0:
                if move_item_robust(item.Serial, container_serial, amount):
                    dropped_count += 1

    return dropped_count


def find_salvage_bag():
    """
    Find a salvage bag in the player's backpack.

    Salvage bags have graphic 0x0E76 and contain "salvage bag" in their name.

    Returns:
        Salvage bag item serial, or None if not found
    """
    bags = API.FindTypeAll(0x0E76, API.Player.Backpack) or []
    for bag in bags:
        # Check if the item has "salvage bag" in its name
        if bag.Name and "salvage bag" in bag.Name.lower():
            return bag.Serial
    return None


def drop_all_items_at_home(container_serial, item_types, extra_sources=None):
    """
    Pathfind to container, open it, and drop items from backpack and optional extra sources.
    Adds delay at end for server to update weight.

    Args:
        container_serial: Destination container serial
        item_types: List of item graphic IDs to move
        extra_sources: Optional list of additional source container serials (e.g., pack animal)

    Returns: total count of item stacks dropped
    """
    # Pathfind to container
    chest = API.FindItem(container_serial)
    if chest:
        API.Pathfind(chest.X, chest.Y, chest.Z, distance=1, wait=True, timeout=10)
        API.Pause(0.5)

    # Open container
    API.UseObject(container_serial)
    API.Pause(1.0)

    total_dropped = 0

    # Drop from backpack
    total_dropped += drop_items_to_container(container_serial, item_types, API.Backpack)

    # Drop from extra sources (e.g., pack animal)
    if extra_sources:
        for source_serial in extra_sources:
            total_dropped += drop_items_to_container(
                container_serial, item_types, source_serial
            )

    if total_dropped > 0:
        API.SysMsg(f"Dropped {total_dropped} item stacks in storage")

    # Wait for server to update weight after dropping items
    API.Pause(1.5)

    return total_dropped
