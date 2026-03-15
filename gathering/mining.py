import time

import API
from _lib.items import drop_all_items_at_home
from _lib.persistence import load_int, save_int
from _lib.recovery import Recovery
from _lib.runebook import Runebook, recall_with_retry, wait_for_travel
from _lib.utils import (
    count_items,
    dismount_if_mounted,
    stop_script,
    use_item_on_target,
)
from _lib.weight import is_heavy, is_overweight

SHOVEL_TYPE = 0x0F39

ORE_TYPES = [0x19B8, 0x19B7, 0x19B9, 0x19BA]
SMALL_ORE_TYPE = 0x19B7

SMELT_OVERWEIGHT_ALLOWANCE = -30
INGOT_DROP_THRESHOLD = 2000

MINING_DELAY = 0.5
SMELT_DELAY = 0.5

MINE_OFFSETS = [
    (1, 1),
    (-1, 1),
    (1, -1),
    (-1, -1),
]

DEPLETED_MSGS = [
    "There is no metal here to mine.",
    "There is no ore here to mine.",
    "You cannot mine there.",
    "You can't mine that.",
]

ALL_DEPLETED_PAUSE = 15.0

FIRE_BEETLE_GRAPHIC = 0x00A9
FIRE_BEETLE_HUE = 1161

INGOT_TYPE = 0x1BF2
BONUS_MINING_ITEMS = [
    0x0DF8,  # Large Jade Stone
    0x0F28,  # A Small Piece of Blackrock
    0x1726,  # Small Jade Stone
    0x3192,  # Dark Sapphire
    0x3193,  # Turquoise
    0x3194,  # Perfect Emerald
    0x3195,  # Ecru Citrine
    0x3197,  # Fire Ruby
    0x3198,  # Blue Diamond
    0x4B4B,  # Cracked Lava Rock
    0x4B4F,  # Cracked Lava Rock
    0x5732,  # Crystalline Blackrock
]
DROP_ITEM_TYPES = [INGOT_TYPE] + BONUS_MINING_ITEMS

USE_SACRED_JOURNEY = False
MAX_TRAVEL_RETRIES = 3
TRAVEL_RETRY_DELAY = 2.0

MAX_CONSECUTIVE_FAILURES = 5
SMELT_NO_PROGRESS_LIMIT = 8


PERSIST_KEY_BEETLE = "Mining.FireBeetleSerial"
PERSIST_KEY_MINING_BOOK = "Mining.MiningRunebookSerial"
PERSIST_KEY_HOME_RUNE = "Mining.HomeRuneSerial"
PERSIST_KEY_DROP_CONTAINER = "Mining.DropContainerSerial"
PERSIST_KEY_CURRENT_SPOT = "Mining.CurrentSpotIndex"


def find_smeltable_ore():
    for ore_type in ORE_TYPES:
        required = 2 if ore_type == SMALL_ORE_TYPE else 1
        ore = API.FindType(ore_type, API.Backpack, minamount=required)
        if ore:
            return ore
    return None


def mine_once(shovel, x_offset: int, y_offset: int) -> bool:
    API.ClearJournal()
    API.UseObject(shovel.Serial)

    if not API.WaitForTarget(timeout=7):
        return False

    API.TargetTileRel(x_offset, y_offset)
    API.Pause(MINING_DELAY)
    return True


def smelt_all_ore(beetle_serial: int) -> int:
    no_progress = 0

    while not API.StopRequested:
        ore = find_smeltable_ore()
        if not ore:
            return beetle_serial

        before_item = API.FindItem(ore.Serial)
        before_amount = (
            before_item.Amount
            if before_item and before_item.Amount is not None
            else None
        )

        API.ClearJournal()

        if API.HasTarget("any"):
            API.CancelTarget()
            API.Pause(0.1)

        if beetle_serial <= 0:
            stop_script("No fire beetle serial set; stopping", 32)
            return 0

        if not use_item_on_target(
            ore.Serial,
            beetle_serial,
            timeout=2.0,
            delay=SMELT_DELAY,
        ):
            no_progress += 1
            API.Pause(SMELT_DELAY)
            continue

        if API.HasTarget("any"):
            API.CancelTarget()
            API.Pause(0.1)
            no_progress += 1
            continue

        if API.InJournal("You must wait"):
            API.Pause(0.5)
            continue

        if API.InJournal("There is not enough metal"):
            API.MoveItemOffset(ore.Serial, 0, 1, 1, 0)
            API.ClearJournal()
            API.Pause(SMELT_DELAY)
            no_progress = 0
            continue

        after_item = API.FindItem(ore.Serial)
        after_amount = (
            after_item.Amount if after_item and after_item.Amount is not None else None
        )

        made_progress = False
        if before_amount is not None:
            made_progress = (after_item is None) or (after_amount != before_amount)
        else:
            made_progress = after_item is None

        if made_progress:
            no_progress = 0
        else:
            no_progress += 1

        if no_progress >= SMELT_NO_PROGRESS_LIMIT:
            detected = find_fire_beetle()
            if detected:
                beetle_serial = detected
                save_int(PERSIST_KEY_BEETLE, beetle)
                no_progress = 0
                continue

            new_beetle = API.RequestTarget()
            if not new_beetle:
                stop_script("No beetle targeted; stopping", 32)
                return beetle_serial

            beetle_serial = int(new_beetle)
            save_int(PERSIST_KEY_BEETLE, beetle)
            no_progress = 0

    return beetle_serial


def find_fire_beetle() -> int:
    mobiles = API.GetAllMobiles(graphic=FIRE_BEETLE_GRAPHIC)
    if not mobiles:
        return 0

    for mob in mobiles:
        if mob.Hue == FIRE_BEETLE_HUE:
            return mob.Serial

    return 0


def wait_for_beetle(timeout: float = 15.0) -> int:
    beetle = find_fire_beetle()
    if beetle:
        return beetle

    deadline = time.time() + timeout

    while time.time() < deadline and not API.StopRequested:
        beetle = find_fire_beetle()
        if beetle:
            return beetle
        API.Pause(1.0)

    return 0


def drop_ore_until_not_overweight() -> None:
    while is_overweight() and not API.StopRequested:
        ore_items = []
        for ore_type in ORE_TYPES:
            ore_items.extend(API.FindTypeAll(ore_type, API.Backpack) or [])

        if not ore_items:
            return

        def sort_key(item):
            amount = getattr(item, "Amount", 0) or 0
            return amount

        ore_items.sort(key=sort_key, reverse=True)
        ore = ore_items[0]

        API.MoveItemOffset(ore.Serial, 0, 1, 1, 0)
        API.Pause(0.75)


def ensure_beetle_or_dump_and_recall(
    beetle_serial: int, home_rune_serial: int, wait_timeout: float = 60.0
) -> int:
    beetle = find_fire_beetle() or beetle_serial

    if not find_fire_beetle():
        beetle = wait_for_beetle(timeout=wait_timeout) or beetle

    if beetle and find_fire_beetle():
        return beetle

    if is_overweight():
        drop_ore_until_not_overweight()

    if home_rune_serial:
        recall_home(home_rune_serial)

    API.Stop()
    return 0


def smelt_before_travel(beetle_serial: int) -> int:
    if find_smeltable_ore():
        beetle_serial = smelt_all_ore(beetle_serial)
    return beetle_serial


def setup_travel_targets():
    mining_book = load_int(PERSIST_KEY_MINING_BOOK, 0)
    if not mining_book:
        mining_book = API.RequestTarget()
        if mining_book:
            save_int(PERSIST_KEY_MINING_BOOK, mining_book)

    home_rune = load_int(PERSIST_KEY_HOME_RUNE, 0)
    if not home_rune:
        home_rune = API.RequestTarget()
        if home_rune:
            save_int(PERSIST_KEY_HOME_RUNE, home_rune)

    drop_container = load_int(PERSIST_KEY_DROP_CONTAINER, 0)
    if not drop_container:
        drop_container = API.RequestTarget()
        if drop_container:
            save_int(PERSIST_KEY_DROP_CONTAINER, drop_container)

    current_spot = load_int(PERSIST_KEY_CURRENT_SPOT, 0)

    return mining_book, home_rune, drop_container, current_spot


def recall_to_mining_spot(runebook: Runebook, index: int) -> bool:
    for attempt in range(1, MAX_TRAVEL_RETRIES + 1):
        if USE_SACRED_JOURNEY:
            success = runebook.sacred_journey_to_index(index)
        else:
            success = runebook.recall_to_index(index)

        if success and wait_for_travel():
            dismount_if_mounted()
            return True

        if attempt < MAX_TRAVEL_RETRIES:
            API.Pause(TRAVEL_RETRY_DELAY)

    return False


def recall_to_next_spot(runebook: Runebook, current_idx: int, max_spots: int) -> tuple:
    next_idx = (current_idx + 1) % max_spots
    save_int(PERSIST_KEY_CURRENT_SPOT, next_idx)
    success = recall_to_mining_spot(runebook, next_idx)
    return success, next_idx


def recall_home(home_serial: int) -> bool:
    return recall_with_retry(
        home_serial,
        max_retries=MAX_TRAVEL_RETRIES,
        retry_delay=TRAVEL_RETRY_DELAY,
        use_sacred_journey=USE_SACRED_JOURNEY,
    )


def is_at_home(container_serial: int) -> bool:
    if not container_serial:
        return False
    return API.FindItem(container_serial) is not None


beetle = find_fire_beetle()

if beetle:
    save_int(PERSIST_KEY_BEETLE, beetle)
else:
    beetle = load_int(PERSIST_KEY_BEETLE, 0)

    if not beetle:
        beetle = API.RequestTarget()
        if beetle:
            save_int(PERSIST_KEY_BEETLE, beetle)

if not beetle:
    stop_script("No beetle targeted; stopping")


mining_runebook_serial, home_rune_serial, drop_container_serial, current_spot_index = (
    setup_travel_targets()
)

mining_runebook = None
if mining_runebook_serial:
    mining_runebook = Runebook(mining_runebook_serial)

max_mining_spots = 16

dismount_if_mounted()

if drop_container_serial and is_at_home(drop_container_serial):
    from _lib.utils import count_items

    ingots = count_items(INGOT_TYPE, API.Backpack)
    if ingots > 0:
        dropped = drop_all_items_at_home(drop_container_serial, DROP_ITEM_TYPES)

if drop_container_serial and is_at_home(drop_container_serial):
    if is_heavy():
        beetle = smelt_before_travel(beetle)
        dropped = drop_all_items_at_home(drop_container_serial, DROP_ITEM_TYPES)

if mining_runebook:
    shovel = API.FindType(SHOVEL_TYPE, API.Backpack)
    if not shovel:
        API.Stop()

    if drop_container_serial and not is_at_home(drop_container_serial):
        current_spot_index = (current_spot_index + 1) % max_mining_spots
        save_int(PERSIST_KEY_CURRENT_SPOT, current_spot_index)

    beetle = smelt_before_travel(beetle)

    if is_overweight():
        API.Stop()

    if not recall_to_mining_spot(mining_runebook, current_spot_index):
        stop_script("Failed to recall to initial mining spot; stopping")

    beetle = wait_for_beetle(timeout=15)
    if not beetle:
        beetle = load_int(PERSIST_KEY_BEETLE, 0)
    if not beetle:
        stop_script("Cannot find beetle after teleport; stopping")

depleted_offsets = set()
consecutive_failures = 0
stuck_checks = 0
recovery = Recovery(home_rune_serial, 120)

while not API.StopRequested:
    if recovery.is_stuck():
        if recovery.shutdown_cleanly():
            break
        stop_script("Stuck and could not recall home")
        break

    shovel = API.FindType(SHOVEL_TYPE, API.Backpack)
    if not shovel:
        if home_rune_serial:
            beetle = smelt_before_travel(beetle)
            recall_with_retry(
                home_rune_serial,
                max_retries=MAX_TRAVEL_RETRIES,
                retry_delay=TRAVEL_RETRY_DELAY,
                use_sacred_journey=USE_SACRED_JOURNEY,
            )
        stop_script("Out of shovels; stopping")
        break

    if is_overweight(SMELT_OVERWEIGHT_ALLOWANCE):
        beetle = ensure_beetle_or_dump_and_recall(beetle, home_rune_serial)
        if not beetle:
            break

        beetle = smelt_all_ore(beetle)
        consecutive_failures = 0

        if count_items(INGOT_TYPE, API.Backpack) >= INGOT_DROP_THRESHOLD:
            if home_rune_serial and drop_container_serial:
                if not recall_home(home_rune_serial):
                    consecutive_failures += 1
                    if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                        if recovery.shutdown_cleanly():
                            break
                        stop_script("Recovery failed - stopping")
                    break

                dropped = drop_all_items_at_home(drop_container_serial, DROP_ITEM_TYPES)
                consecutive_failures = 0

                if dropped == 0:
                    stop_script(
                        "No items to drop but ingot threshold reached; stopping"
                    )
                    break

                if mining_runebook:
                    if not recall_to_mining_spot(mining_runebook, current_spot_index):
                        consecutive_failures += 1
                        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                            if recovery.shutdown_cleanly():
                                break
                            stop_script("Recovery failed - stopping")
                        break

                    beetle = wait_for_beetle(timeout=15)
                    if not beetle:
                        beetle = load_int(PERSIST_KEY_BEETLE, 0)
                    if not beetle:
                        break
                    consecutive_failures = 0
                else:
                    break
            else:
                break

        API.Pause(0.25)
        continue

    if len(depleted_offsets) >= len(MINE_OFFSETS):
        depleted_offsets.clear()

        if mining_runebook:
            beetle = smelt_before_travel(beetle)

            if is_overweight():
                if home_rune_serial and drop_container_serial:
                    if not recall_home(home_rune_serial):
                        break

                    dropped = drop_all_items_at_home(
                        drop_container_serial, DROP_ITEM_TYPES
                    )

                    if dropped == 0:
                        break
                else:
                    break

            success, current_spot_index = recall_to_next_spot(
                mining_runebook, current_spot_index, max_mining_spots
            )

            if not success:
                break

            beetle = wait_for_beetle(timeout=15)
            if not beetle:
                beetle = load_int(PERSIST_KEY_BEETLE)
            if not beetle:
                break
        else:
            API.Pause(ALL_DEPLETED_PAUSE)

        continue

    mined_any = False
    for x_off, y_off in MINE_OFFSETS:
        if (x_off, y_off) in depleted_offsets:
            continue

        mined_any = True
        mine_once(shovel, x_off, y_off)
        consecutive_failures = 0

        API.ClearJournal("$You dig some (.+) ore")

        if API.InJournalAny(DEPLETED_MSGS):
            depleted_offsets.add((x_off, y_off))

        API.Pause(0.25)
        break

    if not mined_any:
        depleted_offsets.clear()
        API.Pause(ALL_DEPLETED_PAUSE)
