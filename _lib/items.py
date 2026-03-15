import json
import re
from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import API


def move_item_robust(serial, dest, amount, max_retries=5):
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
                continue
            else:
                return False

        return True

    return False


def drop_items_to_container(
    container_serial: int, item_types: "list[int]", source=None
):
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
    bags = API.FindTypeAll(0x0E76, API.Player.Backpack) or []
    for bag in bags:
        if bag.Name and "salvage bag" in bag.Name.lower():
            return bag.Serial
    return None


def drop_all_items_at_home(container_serial, item_types, extra_sources=None):
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

    API.Pause(1.5)
    return total_dropped


def chest_check(container_serial=None):
    if container_serial is None:
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


def dump_container_data():
    cont = API.FindItem(API.RequestTarget())
    if not cont:
        API.Stop()

    API.UseObject(cont)
    API.Pause(0.663)

    def container_data():
        try:
            with open("containers.json", "r") as f:
                data = json.load(f)
                return data
        except (ValueError, IOError):
            return defaultdict(list)

    data = container_data()
    data[str(cont.Serial)] = sorted([item.Name for item in API.ItemsInContainer(cont)])

    with open("containers.json", "w") as f:
        json.dump(data, f, indent=2)


def skill_jewelry_finder(min=30):
    for item in API.ItemsInContainer(API.RequestTarget(), recursive=True):
        sum = 0
        for prop in item.NameAndProps(True).split("\n"):
            match = re.match(r"(?:.+) \+(\d+)$", prop)
            if match:
                sum += int(match.group(1))

        if sum > min:
            yield item


def honesty_item_tracker():
    items = API.GetItemsOnGround(24)
    if not items:
        return

    for i, item in enumerate(items):
        tooltip = API.ItemNameAndProps(item)

        if "Lost Item" in tooltip:
            API.HeadMsg("Lost Item!", API.Player)
            API.TrackingArrow(item.X, item.Y, i)

            while item.Distance > 2:
                API.Pathfind(item.X, item.Y, item.Z, 1, True)
                API.Pause(0.1)

            API.MoveItem(item, API.Backpack)
            API.TrackingArrow(-1, -1, i)

    API.Pause(0.1)
