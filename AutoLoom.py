"""
AutoLoom - Automated cloth production using spinning wheel and loom.

This script automates the process of converting raw materials (cotton, flax, wool)
into cloth. It uses a spinning wheel to create thread/yarn from raw materials,
then uses a loom to weave thread/yarn into cloth bolts.

Features:
- Auto-restocks materials from storage container or pack animal
- Tracks spinning wheel completion via journal messages
- Offloads finished cloth when overweight
- Supports both static containers and pack animals
"""
import API
from lib.persistence import setup_target, save_int
from lib.weight import is_heavy
from lib.items import drop_items_to_container, move_item_robust
from lib.utils import find_any_type, stop_script

SPINNING_WHEEL_TYPE = 0x1015
LOOM_TYPES = [0x1061, 0x1062]
RAW_MATERIAL_TYPES = [0xDF8, 0xDF9, 0x1A9C]
THREAD_YARN_TYPES = [0xE1D, 0xE1E, 0xE1F, 0xFA0]
CLOTH_TYPE = 0xF95
LOOM_DELAY = 0.2
WHEEL_COMPLETE_MSGS = ["spools of thread", "spool of thread", "balls of yarn"]
PERSIST_KEY_CONTAINER = "AutoLoom.StorageContainer"


class LoomState:
    def __init__(self):
        self.wheel_ready = True
        self.storage_container = 0

    def check_wheel_completion(self):
        if API.InJournalAny(WHEEL_COMPLETE_MSGS):
            self.wheel_ready = True
            API.ClearJournal()
            return True
        return False


def find_item_on_ground(graphics):
    for graphic in graphics:
        items = API.GetItemsOnGround(2, graphic) or []
        if items:
            return items[0]
    return None


def restock_raw_materials(container_serial):
    API.UseObject(container_serial)
    API.Pause(0.65)

    has_raw = find_any_type(RAW_MATERIAL_TYPES, API.Player.Backpack)

    if not has_raw:
        for graphic in RAW_MATERIAL_TYPES:
            item = API.FindType(graphic, container_serial)
            if item:
                move_item_robust(item.Serial, API.Player.Backpack, 100)
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
    API.UseObject(material.Serial)
    if API.WaitForTarget(timeout=2.0):
        API.Target(station_serial)  # type: ignore
        return True
    return False


def process_spinning_wheel(wheel_serial):
    material = find_any_type(RAW_MATERIAL_TYPES, API.Player.Backpack)
    if material:
        return use_material_on_station(material, wheel_serial)
    return False


def process_loom(loom_serial):
    material = find_any_type(THREAD_YARN_TYPES, API.Player.Backpack)
    if material:
        return use_material_on_station(material, loom_serial)
    return False


def main():
    API.CancelTarget()
    API.Pause(0.1)

    loom = find_item_on_ground(LOOM_TYPES)
    wheel = find_item_on_ground([SPINNING_WHEEL_TYPE])

    if not loom:
        stop_script("Could not find loom nearby")
        return

    if not wheel:
        stop_script("Could not find spinning wheel nearby")
        return

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

    while not API.StopRequested:
        if is_heavy(buffer=50):
            API.UseObject(storage_container)
            API.Pause(0.65)
            drop_items_to_container(storage_container, [CLOTH_TYPE])

        state.check_wheel_completion()

        has_raw = find_any_type(RAW_MATERIAL_TYPES, API.Player.Backpack)
        has_thread = find_any_type(THREAD_YARN_TYPES, API.Player.Backpack)

        # If we have nothing at all and wheel is ready, try to restock
        if not has_raw and not has_thread and state.wheel_ready:
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

        # Restock raw materials if needed and wheel is ready
        if not has_raw and state.wheel_ready:
            restock_raw_materials(storage_container)

        # Always try to keep thread available for the loom
        restock_thread_if_available(storage_container)

        if state.wheel_ready and process_spinning_wheel(wheel.Serial):
            state.wheel_ready = False
            API.Pause(LOOM_DELAY)

        if process_loom(loom.Serial):
            API.Pause(LOOM_DELAY)
            continue

        API.Pause(0.2)


main()
