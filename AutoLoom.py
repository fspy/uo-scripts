"""
AutoLoom - Automated cloth production using spinning wheels and loom.

This script automates the process of converting raw materials (cotton, flax, wool)
into cloth. It uses multiple spinning wheels to create thread/yarn from raw materials,
then uses a loom to weave thread/yarn into cloth bolts.

Features:
- Supports up to 3 spinning wheels for parallel processing
- Timer-based wheel tracking (no journal message dependency)
- Auto-restocks materials from storage container or pack animal
- Offloads finished cloth when overweight
- Supports both static containers and pack animals
"""

import time

import API
from lib.items import drop_items_to_container, move_item_robust
from lib.persistence import save_int, setup_target
from lib.utils import find_any_type, stop_script
from lib.weight import is_heavy

SPINNING_WHEEL_TYPES = [0x1015, 0x1019]
LOOM_TYPES = [0x1061, 0x1062]
RAW_MATERIAL_TYPES = [0xDF8, 0xDF9, 0x1A9C]
THREAD_YARN_TYPES = [0xE1D, 0xE1E, 0xE1F, 0xFA0]
CLOTH_TYPE = 0xF95
LOOM_DELAY = 0.1
WHEEL_PROCESS_TIME = 6.0  # Seconds for wheel to process materials into thread
RAW_MATERIAL_WEIGHT = 4  # Stones per unit of cotton/flax/wool
THREAD_THRESHOLD = 50  # Skip wheel feeding if thread count exceeds this
PERSIST_KEY_CONTAINER = "AutoLoom.StorageContainer"


class WheelState:
    """Tracks a single spinning wheel's state and readiness."""

    def __init__(self, serial):
        self.serial = serial
        self.busy_until = 0.0

    def is_ready(self):
        """Check if wheel has finished processing and is ready for new material."""
        return time.time() >= self.busy_until

    def mark_used(self):
        """Mark wheel as busy, will be ready after WHEEL_PROCESS_TIME seconds."""
        self.busy_until = time.time() + WHEEL_PROCESS_TIME


class LoomState:
    """Holds runtime state for the loom operation."""

    def __init__(self):
        self.storage_container = 0
        self.wheels = []  # List of WheelState objects
        self.loom_failures = 0  # Track consecutive loom failures

    def any_wheel_ready(self):
        """Check if any wheel is ready for new material."""
        return any(wheel.is_ready() for wheel in self.wheels)


def find_item_on_ground(graphics):
    """Find first item matching any graphic within 2 tiles."""
    for graphic in graphics:
        items = API.GetItemsOnGround(2, graphic) or []
        if items:
            return items[0]
    return None


def find_all_items_on_ground(graphics, max_count=3):
    """Find all items matching any graphic within 2 tiles, up to max_count."""
    if not isinstance(graphics, list):
        graphics = [graphics]
    items = []
    for graphic in graphics:
        items.extend(API.GetItemsOnGround(2, graphic) or [])
    return items[:max_count]


def count_thread_in_backpack():
    """Count total thread/yarn in backpack."""
    total = 0
    for graphic in THREAD_YARN_TYPES:
        items = API.FindTypeAll(graphic, API.Player.Backpack) or []
        total += sum(getattr(item, "Amount", 1) for item in items)
    return total


def restock_raw_materials(container_serial):
    # Always dump cloth first to make room
    drop_items_to_container(container_serial, [CLOTH_TYPE])

    API.UseObject(container_serial)
    API.Pause(0.65)

    has_raw = find_any_type(RAW_MATERIAL_TYPES, API.Player.Backpack)

    if not has_raw:
        # Calculate how much we can carry (leave 50 stone buffer)
        available = API.Player.WeightMax - API.Player.Weight - 50
        amount = max(1, available // RAW_MATERIAL_WEIGHT) if available > 0 else 0

        if amount > 0:
            for graphic in RAW_MATERIAL_TYPES:
                item = API.FindType(graphic, container_serial)
                if item:
                    move_item_robust(item.Serial, API.Player.Backpack, amount)
                    has_raw = True
                    break

    return has_raw


def restock_thread_if_available(container_serial):
    has_thread = find_any_type(THREAD_YARN_TYPES, API.Player.Backpack)

    if not has_thread:
        for graphic in THREAD_YARN_TYPES:
            item = API.FindType(graphic, container_serial)
            if item:
                move_item_robust(item.Serial, API.Player.Backpack, 100)
                break


def use_material_on_station(material, station_serial):
    # Clear any lingering target cursor first
    if API.HasTarget():
        API.CancelTarget()
        API.Pause(0.2)

    API.ClearJournal()  # Clear journal before action
    API.UseObject(material.Serial)
    API.Pause(0.1)  # Small delay after using material

    if API.WaitForTarget(timeout=3.0):  # Longer timeout for lag
        API.Target(station_serial)  # type: ignore
        API.Pause(0.2)  # Wait for server response

        # Check for SUCCESS messages (cloth creation or progression)
        if API.InJournal("cloth", False):  # Don't clear journal, just check
            return True

        # Check if target was actually rejected (only if no success message)
        if API.InJournal("Select a", False):
            # Could be rejection OR just the prompt before success
            # If we have cloth messages, ignore the "Select a"
            API.CancelTarget()
            return False

        # No clear success or failure message - assume success
        return True

    # Target cursor never appeared - cancel any pending state
    API.CancelTarget()
    return False


def process_spinning_wheel(wheel_serial):
    material = find_any_type(RAW_MATERIAL_TYPES, API.Player.Backpack)
    if material:
        return use_material_on_station(material, wheel_serial)
    return False


def process_loom(loom_serial):
    """Process loom with the cached serial."""
    material = find_any_type(THREAD_YARN_TYPES, API.Player.Backpack)
    if material:
        return use_material_on_station(material, loom_serial)
    return False


def main():
    API.CancelTarget()
    API.Pause(0.1)

    # Verify loom and wheels exist at startup
    loom = find_item_on_ground(LOOM_TYPES)
    if not loom:
        stop_script("Could not find loom nearby")
        return

    # Find all spinning wheels (up to 3)
    wheel_items = find_all_items_on_ground(SPINNING_WHEEL_TYPES, max_count=3)
    if not wheel_items:
        stop_script("Could not find any spinning wheels nearby")
        return

    API.SysMsg(f"Found {len(wheel_items)} spinning wheel(s)", 946)

    storage_container = setup_target(
        PERSIST_KEY_CONTAINER,
        "Target your storage container or pack animal",
        verify_in_range=True,
    )

    if not storage_container or storage_container == 0:
        stop_script("No container - script stopped")
        return

    mob = API.FindMobile(storage_container)
    if mob and getattr(mob, "Backpack", None):
        storage_container = mob.Backpack.Serial
        save_int(PERSIST_KEY_CONTAINER, storage_container)
        API.SysMsg("Using pack animal backpack", 946)

    state = LoomState()
    state.storage_container = storage_container

    # Initialize wheel trackers
    for wheel_item in wheel_items:
        state.wheels.append(WheelState(wheel_item.Serial))

    loom_serial = loom.Serial  # Cache loom serial for main loop
    API.SysMsg(f"AutoLoom started with {len(state.wheels)} wheel(s) and 1 loom", 946)

    while not API.StopRequested:
        if is_heavy(buffer=20):
            API.UseObject(storage_container)
            API.Pause(0.65)
            drop_items_to_container(storage_container, [CLOTH_TYPE])

        has_raw = find_any_type(RAW_MATERIAL_TYPES, API.Player.Backpack)
        has_thread = find_any_type(THREAD_YARN_TYPES, API.Player.Backpack)
        thread_count = count_thread_in_backpack()

        # Feed all ready wheels FIRST (every loop, regardless of thread count)
        for wheel in state.wheels:
            if wheel.is_ready() and has_raw:
                material = find_any_type(RAW_MATERIAL_TYPES, API.Player.Backpack)
                if material:
                    if use_material_on_station(material, wheel.serial):
                        wheel.mark_used()
                        has_raw = find_any_type(RAW_MATERIAL_TYPES, API.Player.Backpack)
                    else:
                        # Failed to use material - likely out of range
                        API.SysMsg("Failed to use wheel - check position", 33)

        # PRIORITY 1: If we have lots of thread, focus on looming it down
        if thread_count > THREAD_THRESHOLD:
            if has_thread:
                if process_loom(loom_serial):
                    API.Pause(LOOM_DELAY)
                    state.loom_failures = 0  # Reset on success
                else:
                    state.loom_failures += 1
                    API.SysMsg(
                        f"Failed to use loom ({state.loom_failures}) - lag spike?", 33
                    )
                    API.Pause(1.0)  # Longer pause after failure to recover from lag
            API.Pause(0.1)
            continue  # Skip restocking, just keep looming and feeding wheels

        # PRIORITY 2: Normal operation - restock materials and work loom

        # If we have nothing at all and at least one wheel is ready, try to restock
        if not has_raw and not has_thread and state.any_wheel_ready():
            if not restock_raw_materials(storage_container):
                # No materials left in storage - dump everything and stop
                API.SysMsg("No materials available - stopping", 33)
                API.UseObject(storage_container)
                API.Pause(0.65)
                drop_items_to_container(storage_container, [CLOTH_TYPE])
                drop_items_to_container(storage_container, THREAD_YARN_TYPES)
                drop_items_to_container(storage_container, RAW_MATERIAL_TYPES)
                API.SysMsg("Dumped materials to container", 946)
                stop_script("Script finished - no more materials")
                return
            has_raw = True  # We just restocked

        # Restock raw materials if needed and at least one wheel is ready
        if not has_raw and state.any_wheel_ready():
            restock_raw_materials(storage_container)

        # Always try to keep thread available for the loom
        restock_thread_if_available(storage_container)

        # Work the loom if we have thread
        if has_thread:
            if process_loom(loom_serial):
                API.Pause(LOOM_DELAY)
                state.loom_failures = 0  # Reset on success
            else:
                state.loom_failures += 1
                API.SysMsg(
                    f"Failed to use loom ({state.loom_failures}) - lag spike?", 33
                )
                API.Pause(2.0)  # Longer pause after failure to recover from lag

        API.Pause(0.1)


main()
