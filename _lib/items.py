"""Shared item moving utilities for Legion scripts."""

# pyright: basic
try:
    import API
except (ImportError, NameError):
    pass

from _lib.utils import h


def move_item_robust(serial, dest, amount, max_retries=5):
    """Move item with retry logic for 'you must wait' messages."""
    base_delay = 0.6
    max_delay = 1.5
    delay_increment = 0.1

    for attempt in range(max_retries):
        API.ClearJournal()
        API.MoveItem(serial, dest, amt=amount)

        current_delay = min(base_delay + (attempt * delay_increment), max_delay)
        API.Pause(current_delay)

        if API.InJournalAny(["you must wait"]):
            if attempt < max_retries - 1:
                h("Waiting...", API.Player, 946)
                continue
            else:
                return False

        return True

    return False


def drop_items_to_container(
    container_serial: int, item_types: "list[int]", source=None
):
    """Move all items of specified types to a container. Returns count dropped."""
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
    """Find a salvage bag in the player's backpack."""
    bags = API.FindTypeAll(0x0E76, API.Player.Backpack) or []
    for bag in bags:
        if bag.Name and "salvage bag" in bag.Name.lower():
            return bag.Serial
    return None


def drop_all_items_at_home(container_serial, item_types, extra_sources=None):
    """Pathfind to container, open it, and drop items from backpack."""
    chest = API.FindItem(container_serial)
    if chest:
        API.Pathfind(chest.X, chest.Y, chest.Z, distance=1, wait=True, timeout=10)
        API.Pause(0.5)

    API.UseObject(container_serial)
    API.Pause(1.0)

    total_dropped = 0
    total_dropped += drop_items_to_container(container_serial, item_types, API.Backpack)

    if extra_sources:
        for source_serial in extra_sources:
            API.UseObject(source_serial)
            API.Pause(0.5)
            total_dropped += drop_items_to_container(
                container_serial, item_types, source_serial
            )

    if total_dropped > 0:
        API.SysMsg(f"Dropped {total_dropped} item stacks in storage")

    API.Pause(1.5)
    return total_dropped


def chest_check(container_serial=None):
    """Move specific chest types from a container to backpack."""
    if container_serial is None:
        h("Select container to check", API.Player, 946)
        container_serial = API.RequestTarget()
        if not container_serial:
            return

    chest_graphics = {0x0E40, 0x0E41}
    chest_hues = {0, 1109}

    for cg in chest_graphics:
        chests = API.FindTypeAll(cg, container_serial)
        chests = filter(lambda c: c.Hue in chest_hues, chests)
        for chest in chests:
            API.MoveItem(chest, API.Backpack, 1)
            API.Pause(0.65)

        API.Pause(0.65)
