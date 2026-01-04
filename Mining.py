import API
import time
from lib.runebook import Runebook, wait_for_travel, recall_and_target
from lib.items import drop_all_items_at_home
from lib.persistence import load_int, save_int
from lib.weight import is_heavy, is_at_max_weight
from lib.utils import find_any_type

# =========================
# CONFIG
# =========================

# Mine using shovels only (stop script when out).
SHOVEL_TYPE = 0x0F39

# Ore graphics (update for your shard if needed)
# Note: 0x19B7 is the "small" ore pile and often needs 2+ to smelt.
ORE_TYPES = [0x19B8, 0x19B7, 0x19B9, 0x19BA]
SMALL_ORE_TYPE = 0x19B7

# When your weight is within this many stones of max,
# stop mining and smelt on the beetle.
# Note: is_heavy() function from lib.weight uses default buffer of 50 stones
WEIGHT_BUFFER = 50

MINING_DELAY = 0.5
SMELT_DELAY = 0.5

# If you're standing at the crosspoint of 4 adjacent 8x8 resource grids,
# these 4 diagonal tiles typically land inside each grid.
MINE_OFFSETS = [
    (1, 1),
    (-1, 1),
    (1, -1),
    (-1, -1),
]

# Journal texts that indicate the current tile has no ore left.
DEPLETED_MSGS = [
    "There is no metal here to mine.",
    "There is no ore here to mine.",
    "You cannot mine there.",
]

# How long to wait after all 4 tiles are depleted.
# NOTE: This is replaced by runebook travel when enabled
ALL_DEPLETED_PAUSE = 15.0

# =========================
# TRAVEL & RUNEBOOK CONFIG
# =========================

# Fire Beetle auto-detection
FIRE_BEETLE_GRAPHIC = 0x00A9
FIRE_BEETLE_HUE = 1161

# Items to drop at home storage
INGOT_TYPE = 0x1BF2
BONUS_MINING_ITEMS = [
    0x1726,  # Small Jade Stone
    0x3192,  # Dark Sapphire
    0x3193,  # Turquoise
    0x3195,  # Ecru Citrine
    0x3197,  # Fire Ruby
    0x3198,  # Blue Diamond
    0x4B4B,  # Cracked Lava Rock
]
DROP_ITEM_TYPES = [INGOT_TYPE] + BONUS_MINING_ITEMS

# Travel settings
USE_SACRED_JOURNEY = False  # True = Chivalry Sacred Journey, False = Magery Recall
MAX_TRAVEL_RETRIES = 3
TRAVEL_RETRY_DELAY = 2.0  # Seconds between retry attempts

# Weight and item finding functions moved to lib modules (lib.weight, lib.utils)

def find_shovel():
    return API.FindType(SHOVEL_TYPE, API.Backpack)


def find_any_ore(min_amount: int = 0):
    """Find any ore type in backpack. Wrapper for lib.utils.find_any_type."""
    return find_any_type(ORE_TYPES, API.Backpack, min_amount=min_amount)


def find_smeltable_ore():
    # On this shard, the small ore pile (0x19B7) needs at least 2.
    for ore_type in ORE_TYPES:
        required = 2 if ore_type == SMALL_ORE_TYPE else 1
        ore = API.FindType(ore_type, API.Backpack, minamount=required)
        if ore:
            return ore
    return None


def should_mark_depleted() -> bool:
    return API.InJournalAny(DEPLETED_MSGS)


def mine_once(shovel, x_offset: int, y_offset: int) -> bool:
    API.ClearJournal()
    API.UseObject(shovel.Serial)

    if not API.WaitForTarget(timeout=7):
        return False

    API.TargetTileRel(x_offset, y_offset)
    API.Pause(MINING_DELAY)
    return True


SMELT_NO_PROGRESS_LIMIT = 8


def smelt_all_ore(beetle_serial: int) -> int:
    # Smelt everything we can.
    # Small ore (0x19B7) requires 2+; other ore types can smelt at 1.
    # Returns (possibly updated) beetle serial.
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

        # Use ore and wait for target cursor
        API.UseObject(ore.Serial)

        if not API.WaitForTarget(timeout=2.0):
            # No target cursor appeared - server might be lagging
            API.Pause(SMELT_DELAY)
            continue

        # Target the beetle
        API.Target(beetle_serial)  # type: ignore
        API.Pause(SMELT_DELAY)

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
            API.SysMsg("Smelting made no progress; retarget your fire beetle")
            new_beetle = API.RequestTarget()
            if not new_beetle:
                API.SysMsg("No beetle targeted; stopping")
                API.Stop()
                return beetle_serial

            beetle_serial = int(new_beetle)
            save_beetle_serial(beetle_serial)
            API.SysMsg(f"Updated beetle serial: {hex(beetle_serial)}")
            no_progress = 0

    return beetle_serial


# =========================
# PERSISTENT VARIABLES
# =========================

PERSIST_KEY_BEETLE = "Mining.FireBeetleSerial"
PERSIST_KEY_MINING_BOOK = "Mining.MiningRunebookSerial"
PERSIST_KEY_HOME_RUNE = "Mining.HomeRuneSerial"
PERSIST_KEY_DROP_CONTAINER = "Mining.DropContainerSerial"
PERSIST_KEY_CURRENT_SPOT = "Mining.CurrentSpotIndex"


# Persistence helpers moved to lib/persistence.py


def load_beetle_serial() -> int:
    """Load beetle serial from persistent storage."""
    return load_int(PERSIST_KEY_BEETLE, 0)


def save_beetle_serial(serial: int) -> None:
    """Save beetle serial to persistent storage."""
    save_int(PERSIST_KEY_BEETLE, serial)


# =========================
# FIRE BEETLE AUTO-DETECTION
# =========================


def find_fire_beetle() -> int:
    """
    Find nearest fire beetle by graphic and hue.
    Returns serial or 0 if not found.
    """
    mobiles = API.GetAllMobiles(graphic=FIRE_BEETLE_GRAPHIC)
    if not mobiles:
        return 0

    for mob in mobiles:
        if mob.Hue == FIRE_BEETLE_HUE:
            return mob.Serial

    return 0


def wait_for_beetle(timeout: float = 15.0) -> int:
    """
    Wait for fire beetle to arrive after recall.
    Returns serial or 0 if timeout.
    """
    # First check if beetle is already here
    beetle = find_fire_beetle()
    if beetle:
        return beetle

    API.SysMsg("Waiting for beetle to arrive...")
    deadline = time.time() + timeout

    while time.time() < deadline and not API.StopRequested:
        beetle = find_fire_beetle()
        if beetle:
            API.SysMsg("Beetle arrived!")
            return beetle
        API.Pause(1.0)

    API.SysMsg("Beetle did not arrive within timeout", 32)
    return 0


def smelt_before_travel(beetle_serial: int) -> int:
    """
    Smelt all ore before traveling to reduce weight.
    Returns (possibly updated) beetle serial.
    """
    if find_smeltable_ore():
        API.SysMsg("Smelting before travel...")
        beetle_serial = smelt_all_ore(beetle_serial)

    # Check if at max weight after smelting
    if is_at_max_weight():
        API.SysMsg("WARNING: At max weight after smelting - recall may fail!", 32)

    return beetle_serial


def dismount_if_mounted() -> None:
    """Dismount if currently mounted (mining requires being on foot)."""
    if API.Player.Mount:
        API.Dismount()
        API.Pause(0.5)


# =========================
# TRAVEL FUNCTIONS
# =========================


def setup_travel_targets():
    """
    Load or prompt for mining runebook, home rune, and drop container.
    Returns: (mining_runebook_serial, home_rune_serial, drop_container_serial, current_spot_index)
    """
    # Load mining runebook
    mining_book = load_int(PERSIST_KEY_MINING_BOOK, 0)
    if not mining_book:
        API.SysMsg("Target your mining runebook (with all mining spots)")
        mining_book = API.RequestTarget()
        if mining_book:
            save_int(PERSIST_KEY_MINING_BOOK, mining_book)
            API.SysMsg(f"Saved mining runebook: {hex(mining_book)}")
        else:
            API.SysMsg("No mining runebook targeted")
    else:
        API.SysMsg(f"Using saved mining runebook: {hex(mining_book)}")

    # Load home rune/book
    home_rune = load_int(PERSIST_KEY_HOME_RUNE, 0)
    if not home_rune:
        API.SysMsg("Target your home rune or runebook (for banking)")
        home_rune = API.RequestTarget()
        if home_rune:
            save_int(PERSIST_KEY_HOME_RUNE, home_rune)
            API.SysMsg(f"Saved home rune: {hex(home_rune)}")
        else:
            API.SysMsg("No home rune targeted")
    else:
        API.SysMsg(f"Using saved home rune: {hex(home_rune)}")

    # Load drop container
    drop_container = load_int(PERSIST_KEY_DROP_CONTAINER, 0)
    if not drop_container:
        API.SysMsg("Target your storage container at home (for dropping ingots)")
        drop_container = API.RequestTarget()
        if drop_container:
            save_int(PERSIST_KEY_DROP_CONTAINER, drop_container)
            API.SysMsg(f"Saved drop container: {hex(drop_container)}")
        else:
            API.SysMsg("No drop container targeted")
    else:
        API.SysMsg(f"Using saved drop container: {hex(drop_container)}")

    # Load current spot index
    current_spot = load_int(PERSIST_KEY_CURRENT_SPOT, 0)
    API.SysMsg(f"Current mining spot index: {current_spot}")

    return mining_book, home_rune, drop_container, current_spot


def recall_to_mining_spot(runebook: Runebook, index: int) -> bool:
    """
    Recall to a specific mining spot with retry logic.
    Returns True if successful, False otherwise.
    """
    for attempt in range(1, MAX_TRAVEL_RETRIES + 1):
        API.SysMsg(
            f"Recalling to mining spot {index} (attempt {attempt}/{MAX_TRAVEL_RETRIES})"
        )

        if USE_SACRED_JOURNEY:
            success = runebook.sacred_journey_to_index(index)
        else:
            success = runebook.recall_to_index(index)

        if success and wait_for_travel():
            API.SysMsg(f"Successfully recalled to spot {index}")
            dismount_if_mounted()
            return True

        if attempt < MAX_TRAVEL_RETRIES:
            API.SysMsg(f"Travel failed, retrying in {TRAVEL_RETRY_DELAY}s...")
            API.Pause(TRAVEL_RETRY_DELAY)

    API.SysMsg(f"Failed to recall to spot {index} after {MAX_TRAVEL_RETRIES} attempts")
    return False


def recall_to_next_spot(runebook: Runebook, current_idx: int, max_spots: int) -> tuple:
    """
    Cycle to next mining spot and recall there.
    Returns: (success: bool, new_index: int)
    """
    next_idx = (current_idx + 1) % max_spots
    API.SysMsg(f"All tiles depleted, moving to next spot: {current_idx} -> {next_idx}")

    # Save the new index before traveling
    save_int(PERSIST_KEY_CURRENT_SPOT, next_idx)

    success = recall_to_mining_spot(runebook, next_idx)
    return success, next_idx


def recall_home(home_serial: int) -> bool:
    """
    Cast Recall or Sacred Journey and target the home rune/book.
    Returns True if successful, False otherwise.
    """
    for attempt in range(1, MAX_TRAVEL_RETRIES + 1):
        API.SysMsg(f"Recalling home (attempt {attempt}/{MAX_TRAVEL_RETRIES})")

        success = recall_and_target(home_serial, USE_SACRED_JOURNEY)

        if success:
            API.SysMsg("Successfully recalled home")
            return True

        if attempt < MAX_TRAVEL_RETRIES:
            API.SysMsg(f"Travel home failed, retrying in {TRAVEL_RETRY_DELAY}s...")
            API.Pause(TRAVEL_RETRY_DELAY)

    API.SysMsg(f"Failed to recall home after {MAX_TRAVEL_RETRIES} attempts")
    return False


def is_at_home(container_serial: int) -> bool:
    """Check if drop container is in range (we're at home)."""
    if not container_serial:
        return False
    return API.FindItem(container_serial) is not None


def drop_items_at_home(container_serial: int, item_types: list) -> int:
    """
    Move all items of specified types to the storage container.
    Pathfinds to container, opens it, then moves items.
    Returns: count of item stacks dropped
    """
    return drop_all_items_at_home(container_serial, item_types)


# =========================
# BEETLE INITIALIZATION
# =========================

# Try to auto-detect beetle first
beetle = find_fire_beetle()

if beetle:
    API.SysMsg(f"Auto-detected fire beetle: {hex(beetle)}")
    # Save for future use
    save_beetle_serial(beetle)
else:
    # Fall back to saved serial
    beetle = load_beetle_serial()

    if not beetle:
        # Finally, prompt for manual targeting
        API.SysMsg("Target your fire beetle (for smelting)")
        beetle = API.RequestTarget()
        if beetle:
            save_beetle_serial(beetle)
    else:
        API.SysMsg(f"Using saved beetle serial: {hex(beetle)}")

# Don't force retarget on startup.
# The client might not be aware of the beetle yet (range/visibility), but the serial
# can still be valid. We'll only prompt to retarget if smelting makes no progress.

if not beetle:
    API.SysMsg("No beetle targeted; stopping")
    API.Stop()

API.SysMsg("Mining started (will smelt when heavy)")

# =========================
# TRAVEL TARGET INITIALIZATION
# =========================

# Setup travel targets (mining runebook, home rune, drop container)
mining_runebook_serial, home_rune_serial, drop_container_serial, current_spot_index = (
    setup_travel_targets()
)

# Initialize Runebook wrapper if we have a mining runebook
mining_runebook = None
if mining_runebook_serial:
    mining_runebook = Runebook(mining_runebook_serial)
    API.SysMsg(f"Mining runebook initialized (current spot: {current_spot_index})")

# Determine max spots (16 runes per runebook, 0-indexed)
max_mining_spots = 16

# Dismount before starting (mining requires being on foot)
dismount_if_mounted()

# Handle dirty state: if at home and heavy, dump first
if drop_container_serial and is_at_home(drop_container_serial):
    if is_heavy():
        API.SysMsg("Starting at home while heavy - dumping items first")
        beetle = smelt_before_travel(beetle)
        dropped = drop_items_at_home(drop_container_serial, DROP_ITEM_TYPES)
        if dropped > 0:
            API.SysMsg(f"Dumped {dropped} item stacks before starting")

# Recall to current mining spot before starting (if runebook configured)
if mining_runebook:
    # Smelt any ore before traveling
    beetle = smelt_before_travel(beetle)

    if is_at_max_weight():
        API.SysMsg("Cannot recall - at max weight; stopping", 32)
        API.Stop()

    API.SysMsg(f"Recalling to mining spot {current_spot_index}...")
    if not recall_to_mining_spot(mining_runebook, current_spot_index):
        API.SysMsg("Failed to recall to initial mining spot; stopping")
        API.Stop()

    # Wait for beetle to arrive after teleport
    beetle = wait_for_beetle(timeout=15)
    if not beetle:
        beetle = load_beetle_serial()  # Fall back to saved serial
    if not beetle:
        API.SysMsg("Cannot find beetle after teleport; stopping")
        API.Stop()

# Track depletion per offset so we can rotate through all 4 directions.
depleted_offsets = set()

while not API.StopRequested:
    shovel = find_shovel()
    if not shovel:
        API.SysMsg("Out of shovels; stopping")
        break

    if is_heavy():
        API.SysMsg("Heavy -> smelting on beetle")
        beetle = smelt_all_ore(beetle)

        # If we're still heavy but there's nothing left we can smelt,
        # travel home to drop items (if travel is configured)
        if is_heavy() and not find_smeltable_ore():
            if home_rune_serial and drop_container_serial:
                API.SysMsg("Still heavy after smelting -> banking ingots at home")

                # Travel home
                if not recall_home(home_rune_serial):
                    API.SysMsg("Failed to recall home; stopping")
                    break

                # Drop ingots and other configured items
                dropped = drop_items_at_home(drop_container_serial, DROP_ITEM_TYPES)

                if dropped == 0:
                    API.SysMsg("No items to drop but still heavy; stopping")
                    break

                # Return to current mining spot
                if mining_runebook:
                    if not recall_to_mining_spot(mining_runebook, current_spot_index):
                        API.SysMsg("Failed to return to mining spot; stopping")
                        break

                    # Wait for beetle to arrive after teleport
                    beetle = wait_for_beetle(timeout=15)
                    if not beetle:
                        beetle = load_beetle_serial()  # Fall back to saved serial
                    if not beetle:
                        API.SysMsg("Cannot find beetle after teleport; stopping")
                        break
                else:
                    API.SysMsg("No mining runebook configured; cannot return to spot")
                    break
            else:
                API.SysMsg("Still heavy but no home/container configured; stopping")
                break

        API.Pause(0.25)
        continue

    # If all 4 tiles are depleted, travel to next spot (if runebook configured)
    if len(depleted_offsets) >= len(MINE_OFFSETS):
        depleted_offsets.clear()

        if mining_runebook:
            API.SysMsg("All 4 mining tiles depleted")

            # Smelt ore before traveling (while beetle is still here)
            beetle = smelt_before_travel(beetle)

            # Check if at max weight after smelting
            if is_at_max_weight():
                API.SysMsg("At max weight - need to bank before traveling")
                if home_rune_serial and drop_container_serial:
                    # Travel home
                    if not recall_home(home_rune_serial):
                        API.SysMsg("Failed to recall home; stopping")
                        break

                    # Drop ingots
                    dropped = drop_items_at_home(drop_container_serial, DROP_ITEM_TYPES)

                    if dropped == 0:
                        API.SysMsg("No items to drop but still at max weight; stopping")
                        break
                else:
                    API.SysMsg("At max weight but no home configured; stopping")
                    break

            API.SysMsg("Traveling to next spot")

            # Recall to next spot and update index
            success, current_spot_index = recall_to_next_spot(
                mining_runebook, current_spot_index, max_mining_spots
            )

            if not success:
                API.SysMsg("Failed to travel to next spot; stopping")
                break

            # Wait for beetle to arrive after teleport
            beetle = wait_for_beetle(timeout=15)
            if not beetle:
                beetle = load_beetle_serial()  # Fall back to saved serial
            if not beetle:
                API.SysMsg("Cannot find beetle after teleport; stopping")
                break
        else:
            # No runebook configured, fall back to waiting
            API.SysMsg("All 4 mining tiles depleted; waiting")
            API.Pause(ALL_DEPLETED_PAUSE)

        continue

    mined_any = False
    for x_off, y_off in MINE_OFFSETS:
        if (x_off, y_off) in depleted_offsets:
            continue

        mined_any = True
        mine_once(shovel, x_off, y_off)

        if should_mark_depleted():
            depleted_offsets.add((x_off, y_off))

        API.Pause(0.25)
        break

    if not mined_any:
        # Shouldn't happen, but prevents a tight loop.
        depleted_offsets.clear()
        API.Pause(ALL_DEPLETED_PAUSE)

API.SysMsg("Mining script finished")
