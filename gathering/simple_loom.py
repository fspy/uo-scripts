import API
from _lib.items import move_item_robust
from _lib.persistence import save_int, setup_target
from _lib.utils import use_item_on_target
from _lib.weight import is_heavy

# Item types
WHEELS = [0x1015, 0x1019]
LOOMS = [0x1061, 0x1062]
RAW = [0xDF8, 0xDF9, 0x1A9C]  # cotton, flax, wool
THREAD = [0xE1D, 0xE1E, 0xE1F, 0xFA0]
CLOTH = 0xF95
WEIGHT_BUFFER = 50


def find_ground(types):
    """Find all items of given types within 2 tiles."""
    results = []
    for t in types:
        items = API.GetItemsOnGround(2, t) or []
        results.extend(items)
    return results


def find_item(types):
    """Find first item of given types in backpack."""
    for t in types:
        item = API.FindType(t, API.Player.Backpack)
        if item:
            return item
    return None


def dump_cloth(container):
    """Dump all cloth to container."""
    API.UseObject(container)
    API.Pause(0.6)
    while True:
        cloth = API.FindType(CLOTH, API.Player.Backpack)
        if not cloth:
            break
        move_item_robust(cloth.Serial, container, cloth.Amount or 1)


def restock_raw(container):
    """Grab raw materials from container. Returns True if found any."""
    API.UseObject(container)
    API.Pause(0.6)

    found_any = False
    for raw_type in RAW:
        item = API.FindType(raw_type, container)
        if item:
            # Grab 100 of this type
            move_item_robust(item.Serial, API.Player.Backpack, 100)
            found_any = True
            break  # Just grab one type at a time

    return found_any


def main():
    API.CancelTarget()
    API.Pause(0.1)

    # Find stations
    wheels = find_ground(WHEELS)
    looms = find_ground(LOOMS)

    if not wheels:
        API.SysMsg("No spinning wheels found nearby!", 33)
        return

    if not looms:
        API.SysMsg("No loom found nearby!", 33)
        return

    loom = looms[0]  # Just use first loom

    API.SysMsg(f"Found {len(wheels)} wheel(s) and 1 loom", 946)

    # Setup container (prompt once, saves for next run)
    container = setup_target(
        "SimpleLoom.Container",
        "Target your storage container or pack animal",
        verify_in_range=True,
    )

    if not container:
        API.SysMsg("No container selected - stopping", 33)
        return

    # Handle pack animals
    mob = API.FindMobile(container)
    if mob and getattr(mob, "Backpack", None):
        container = mob.Backpack.Serial
        save_int("SimpleLoom.Container", container)
        API.SysMsg("Using pack animal backpack", 946)

    API.SysMsg("SimpleLoom started - spam mode engaged!", 946)

    # Main loop
    while not API.StopRequested:
        # Dump cloth if getting heavy
        if is_heavy(buffer=WEIGHT_BUFFER):
            dump_cloth(container)

        # Try to use raw materials on each wheel
        # Server will reject with "you must wait" if wheel is busy - that's fine
        for wheel in wheels:
            raw = find_item(RAW)
            if raw:
                use_item_on_target(raw.Serial, wheel.Serial, timeout=1.0, delay=0.1)

        # Try to use thread on loom
        thread = find_item(THREAD)
        if thread:
            use_item_on_target(thread.Serial, loom.Serial, timeout=1.0, delay=0.1)

        # If we're out of both raw and thread, try to restock
        if not find_item(RAW) and not find_item(THREAD):
            if not restock_raw(container):
                # No materials left in container
                API.SysMsg("Out of materials - dumping and stopping", 33)
                dump_cloth(container)
                API.SysMsg("SimpleLoom finished", 946)
                return

        API.Pause(0.05)


main()
