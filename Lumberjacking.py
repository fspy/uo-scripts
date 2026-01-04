# pyright: reportCallIssue=false

import time
import API
from lib.items import move_item_robust, drop_items_to_container
from lib.persistence import setup_target
from lib.weight import is_heavy, is_overweight
from lib.utils import count_items, stop_script, chebyshev_distance
from lib.journal import wait_for_any
from lib.runebook import recall_and_target, TRAVEL_FAIL_MSGS

# =========================
# CONFIG
# =========================

# Tree tile graphics from ServUO source for reliable detection.
# If your shard uses custom tree graphics, extend this list.
tree_graphics = set(
    [
        0x4CCA,
        0x4CCB,
        0x4CCC,
        0x4CCD,
        0x4CD0,
        0x4CD3,
        0x4CD6,
        0x4CD8,
        0x4CDA,
        0x4CDD,
        0x4CE0,
        0x4CE3,
        0x4CE6,
        0x4CF8,
        0x4CFB,
        0x4CFE,
        0x4D01,
        0x4D41,
        0x4D42,
        0x4D43,
        0x4D44,
        0x4D57,
        0x4D58,
        0x4D59,
        0x4D5A,
        0x4D5B,
        0x4D6E,
        0x4D6F,
        0x4D70,
        0x4D71,
        0x4D72,
        0x4D84,
        0x4D85,
        0x4D86,
        0x52B5,
        0x52B6,
        0x52B7,
        0x52B8,
        0x52B9,
        0x52BA,
        0x52BB,
        0x52BC,
        0x52BD,
        0x4CCE,
        0x4CCF,
        0x4CD1,
        0x4CD2,
        0x4CD4,
        0x4CD5,
        0x4CD7,
        0x4CD9,
        0x4CDB,
        0x4CDC,
        0x4CDE,
        0x4CDF,
        0x4CE1,
        0x4CE2,
        0x4CE4,
        0x4CE5,
        0x4CE7,
        0x4CE8,
        0x4CF9,
        0x4CFA,
        0x4CFC,
        0x4CFD,
        0x4CFF,
        0x4D00,
        0x4D02,
        0x4D03,
        0x4D45,
        0x4D46,
        0x4D47,
        0x4D48,
        0x4D49,
        0x4D4A,
        0x4D4B,
        0x4D4C,
        0x4D4D,
        0x4D4E,
        0x4D4F,
        0x4D50,
        0x4D51,
        0x4D52,
        0x4D53,
        0x4D5C,
        0x4D5D,
        0x4D5E,
        0x4D5F,
        0x4D60,
        0x4D61,
        0x4D62,
        0x4D63,
        0x4D64,
        0x4D65,
        0x4D66,
        0x4D67,
        0x4D68,
        0x4D69,
        0x4D73,
        0x4D74,
        0x4D75,
        0x4D76,
        0x4D77,
        0x4D78,
        0x4D79,
        0x4D7A,
        0x4D7B,
        0x4D7C,
        0x4D7D,
        0x4D7E,
        0x4D7F,
        0x4D87,
        0x4D88,
        0x4D89,
        0x4D8A,
        0x4D8B,
        0x4D8C,
        0x4D8D,
        0x4D8E,
        0x4D8F,
        0x4D90,
        0x4D95,
        0x4D96,
        0x4D97,
        0x4D99,
        0x4D9A,
        0x4D9B,
        0x4D9D,
        0x4D9E,
        0x4D9F,
        0x4DA1,
        0x4DA2,
        0x4DA3,
        0x4DA5,
        0x4DA6,
        0x4DA7,
        0x4DA9,
        0x4DAA,
        0x4DAB,
        0x52BE,
        0x52BF,
        0x52C0,
        0x52C1,
        0x52C2,
        0x52C3,
        0x52C4,
        0x52C5,
        0x52C6,
        0x52C7,
    ]
)

# Debug mode - set to True for verbose logging
DEBUG = False

# Bonus lumberjacking resources to deposit at home
bonus_lumberjack_items = [
    0x5738,  # Crystal Shards
    0x3191,  # Luminescent Fungi
    0x3190,  # Parasitic Plant
    0x318F,  # Bark Fragment
    0x318B,  # Diseased Bark
    0x2F5F,  # Switch
    0x3199,  # Brilliant Amber
    0x3198,  # Blue Diamond
    0x3197,  # Fire Ruby
]

# Journal messages
success_msgs = [
    "and put them in your backpack",
    "fail to produce any useable wood",
]

depleted_msgs = [
    "not enough wood here to harvest",
    "too far away",
    "cannot see that",
    "can't use an axe on that",
    "cannot use an axe on that",
]

wait_msgs = [
    "you must wait",
]

# Travel constants moved to lib.runebook

# =========================
# STATE
# =========================


class LumberjackState:
    """Holds all runtime state for the lumberjacking session."""

    def __init__(self):
        self.depleted_until = {}  # (x,y) -> expiry timestamp
        self.tree_attempts = {}  # (x,y) -> attempt count
        self.last_warn_time = 0.0
        self.no_trees_count = 0  # Track consecutive "no trees nearby" failures

        # Persisted item serials
        self.axe_serial = 0
        self.pack_serial = 0
        self.runebook_serial = 0
        self.drop_chest_serial = 0
        self.rune_serial = 0

        # Bad tree graphics that caused "can't use axe" errors
        self.bad_graphics = set()


# =========================
# HELPERS
# =========================



# Utility functions moved to lib modules (lib.utils, lib.weight, lib.journal)

# is_heavy() function moved to lib.weight (uses 50 stone buffer by default)
# Lumberjacking uses 60 stones - calls pass buffer=60 explicitly

def is_pack_in_range(state):
    """Check if pack animal backpack is in range."""
    if not state.pack_serial:
        return False
    return API.FindItem(state.pack_serial) is not None


def wait_for_pack(state, timeout=30):
    """Wait for pack animal to return. Returns True if pack is back in range."""
    if is_pack_in_range(state):
        return True

    API.HeadMsg("Waiting for pack...", API.Player.Serial, 946)

    deadline = time.time() + timeout
    while time.time() < deadline and not API.StopRequested:
        if is_pack_in_range(state):
            API.HeadMsg("Pack is back!", API.Player.Serial, 62)
            return True
        API.Pause(1.0)

    return False





def warn_weight(state):
    """Warn player about weight status (throttled)."""
    if not is_heavy(buffer=60):
        return

    now = time.time()
    if now - state.last_warn_time < 5.0:
        return

    state.last_warn_time = now

    if is_overweight():
        API.HeadMsg(
            f"OVERWEIGHT! {API.Player.Weight}/{API.Player.WeightMax}",
            API.Player.Serial,
            32,
        )
    else:
        API.HeadMsg(
            f"Heavy! {API.Player.Weight}/{API.Player.WeightMax}",
            API.Player.Serial,
            946,
        )


# =========================
# SETUP FUNCTIONS (using lib/persistence)
# =========================


def is_first_run():
    """Check if this is the first run (no persisted chest serial)."""
    saved = API.GetPersistentVar("LumberjackDropChest", "0", API.PersistentVar.Char)
    return not saved or saved == "0"


def load_bad_graphics():
    """Load persisted bad graphics from char-specific storage."""
    saved = API.GetPersistentVar("LumberjackBadGraphics", "", API.PersistentVar.Char)
    if not saved:
        return set()

    bad = set()
    for part in saved.split(","):
        part = part.strip()
        if part:
            try:
                bad.add(int(part, 16))
            except ValueError:
                pass
    return bad


def save_bad_graphics(state):
    """Save bad graphics to char-specific storage."""
    if not state.bad_graphics:
        return

    hex_list = ",".join(f"0x{g:X}" for g in sorted(state.bad_graphics))
    API.SavePersistentVar("LumberjackBadGraphics", hex_list, API.PersistentVar.Char)


def setup_drop_chest(first_run):
    """
    Setup drop chest with special handling for out-of-range scenarios.

    On first run: Must verify chest exists (needs to be in range)
    On subsequent runs: Trust persisted serial even if out of range
    """
    # On first run, verify the chest is in range. On subsequent runs, trust saved serial.
    return setup_target(
        "LumberjackDropChest",
        "Target drop chest at home",
        verify_in_range=first_run  # Only verify on first run
    )


def setup_all_items(state, first_run):
    """Setup all required items at script start."""
    API.SysMsg("=== Lumberjacking Setup ===", 946)

    if first_run:
        API.SysMsg("First run detected - please target all items at home", 946)

    # Axe
    state.axe_serial = setup_target("LumberjackAxe", "Target your axe")
    if not state.axe_serial:
        stop_script("Axe setup failed")
        return False

    # Pack animal
    state.pack_serial = setup_target(
        "LumberjackPack", "Target your pack animal or its backpack"
    )
    if not state.pack_serial:
        stop_script("Pack animal setup failed")
        return False

    # Resolve pack to backpack if mobile was targeted
    mob = API.FindMobile(state.pack_serial)
    if mob and getattr(mob, "Backpack", None):
        state.pack_serial = mob.Backpack.Serial
        API.SavePersistentVar(
            "LumberjackPack", str(state.pack_serial), API.PersistentVar.Char
        )
        API.SysMsg(f"Using pack animal backpack: 0x{state.pack_serial:X}")

    # Open pack backpack to ensure contents are loaded
    API.UseObject(state.pack_serial)
    API.Pause(1.0)
    API.SysMsg("Opened pack animal backpack")

    # Runebook
    state.runebook_serial = setup_target(
        "LumberjackRunebook", "Target runebook (default rune = recall home)"
    )
    if not state.runebook_serial:
        stop_script("Runebook setup failed")
        return False

    # Drop chest - special handling for out of range
    state.drop_chest_serial = setup_drop_chest(state, first_run)
    if not state.drop_chest_serial:
        stop_script("Drop chest setup failed")
        return False

    # Rune for marking lumber location
    state.rune_serial = setup_target(
        "LumberjackRune", "Target a blank or recall rune (will be reused for marking)"
    )
    if not state.rune_serial:
        stop_script("Rune setup failed")
        return False

    API.SysMsg("=== Setup Complete ===", 946)
    return True


def wait_for_travel_to_lumber_spot(state, first_run):
    """
    Wait for player to travel away from home before starting main loop.

    On first run: Always wait for player to travel 50+ tiles
    On subsequent runs: Skip if chest is out of range (already in woods)
    """
    # If not first run, check if we're already away from home
    if not first_run:
        chest = API.FindItem(state.drop_chest_serial)
        if not chest:
            # Chest not in range - assume we're already in the woods
            API.SysMsg("Already at lumber spot - starting main loop!", 946)
            return True

    # First run or chest is in range - wait for travel
    home_pos = (API.Player.X, API.Player.Y)
    API.SysMsg("Travel to lumber spot (50+ tiles away) to begin.", 946)

    last_msg_time = time.time()

    while not API.StopRequested:
        dist = chebyshev_distance(API.Player.X, API.Player.Y, home_pos[0], home_pos[1])

        # Update message every 5 seconds
        now = time.time()
        if now - last_msg_time >= 5.0:
            API.SysMsg(f"Waiting for travel... (currently {dist} tiles from home)", 946)
            last_msg_time = now

        # Check if player has traveled far enough
        if dist > 50:
            API.SysMsg("Location change detected - starting main loop!", 946)
            return True

        API.Pause(1.0)

    return False


# =========================
# AXE FUNCTIONS
# =========================


def get_equipped_axe(state):
    """Check if axe is equipped in either hand. Returns equipped axe or None."""
    two_handed = API.FindLayer("TwoHanded")
    if two_handed and two_handed.Serial == state.axe_serial:
        return two_handed

    one_handed = API.FindLayer("OneHanded")
    if one_handed and one_handed.Serial == state.axe_serial:
        return one_handed

    return None


def ensure_axe_equipped(state):
    """Equip axe if not already equipped. Returns equipped axe or None."""
    # Check if already equipped
    equipped = get_equipped_axe(state)
    if equipped:
        return equipped

    # Find axe item
    axe = API.FindItem(state.axe_serial)
    if not axe:
        return None

    # Dismount if mounted
    if API.Player.Mount:
        API.Dismount(skipQueue=True)
        API.Pause(1.0)

    # Clear both hands before equipping
    API.ClearLeftHand()
    API.Pause(1.0)
    API.ClearRightHand()
    API.Pause(1.0)

    # Equip axe
    API.EquipItem(axe.Serial)
    API.Pause(1.0)

    return get_equipped_axe(state)


# =========================
# TREE FUNCTIONS
# =========================


def is_valid_tree(static):
    """Check if static is a harvestable tree."""
    if getattr(static, "IsDestroyed", False):
        return False

    # Direct tree flag (client property)
    if getattr(static, "IsTree", False):
        return True

    # Known tree graphic
    if getattr(static, "Graphic", 0) in tree_graphics:
        return True

    # Impassable vegetation (catches some edge cases)
    if getattr(static, "IsVegetation", False) and getattr(
        static, "IsImpassible", False
    ):
        return True

    return False


def find_nearest_tree(state):
    """Find nearest non-depleted tree within 16 tiles."""
    px, py = API.Player.X, API.Player.Y
    statics = API.GetStaticsInArea(px - 16, py - 16, px + 16, py + 16)

    if not statics:
        return None

    # De-dup by (x,y). Trees often have multiple statics at the same tile.
    # Prefer the Z closest to the player (trunk instead of canopy).
    now = time.time()
    player_z = API.Player.Z
    trees = {}

    for s in statics:
        if not is_valid_tree(s):
            continue

        # Skip bad graphics (can't use axe on these)
        if getattr(s, "Graphic", 0) in state.bad_graphics:
            continue

        key = (s.X, s.Y)

        # Skip depleted trees
        if state.depleted_until.get(key, 0) > now:
            continue

        # Keep candidate closest to player Z
        if key not in trees:
            trees[key] = s
        else:
            existing = trees[key]
            existing_z = getattr(existing, "Z", 0) or 0
            s_z = getattr(s, "Z", 0) or 0
            if abs(s_z - player_z) < abs(existing_z - player_z):
                trees[key] = s

    if not trees:
        return None

    # Sort by distance, return nearest
    return min(trees.values(), key=lambda t: chebyshev_distance(px, py, t.X, t.Y))


def pathfind_to_tree(tree):
    """Pathfind to tree. Returns True if successful."""
    return API.Pathfind(tree.X, tree.Y, tree.Z, distance=1, wait=True, timeout=10)


def mark_depleted(state, tree):
    """Mark tree as depleted for 180 seconds."""
    key = (tree.X, tree.Y)
    state.depleted_until[key] = time.time() + 180.0
    state.tree_attempts.pop(key, None)


def cleanup_depleted(state):
    """Remove expired depletion entries."""
    now = time.time()
    state.depleted_until = {k: v for k, v in state.depleted_until.items() if v > now}
    # Also clean up attempts for trees no longer being tracked
    state.tree_attempts = {
        k: v for k, v in state.tree_attempts.items() if k in state.depleted_until
    }


# =========================
# CHOPPING FUNCTIONS
# =========================


def chop_tree(state, tree):
    """Chop a tree. Returns True if action was sent."""
    axe = ensure_axe_equipped(state)
    if not axe:
        stop_script("Could not equip axe")
        return False

    # If we're already holding a target cursor, just retarget
    if API.HasTarget("any"):
        API.Target(tree.X, tree.Y, tree.Z, tree.Graphic)
        wait_for_any(success_msgs + depleted_msgs + wait_msgs, 1.0)
        return True

    # Clear journal before action to get fresh response
    API.ClearJournal()

    # Manual targeting
    API.UseObject(axe.Serial)

    if API.WaitForTarget(timeout=0.5) or API.HasTarget("any"):
        API.Target(tree.X, tree.Y, tree.Z, tree.Graphic)

    # Wait for server response
    wait_for_any(success_msgs + depleted_msgs + wait_msgs, 1.0)
    return True


def chop_all_logs(state):
    """Convert all logs to boards. Returns True if successful."""
    while not API.StopRequested:
        logs = API.FindTypeAll(0x1BDD, API.Backpack) or []
        if not logs:
            break

        for log in logs:
            if API.StopRequested:
                return False

            API.ClearJournal()

            axe = ensure_axe_equipped(state)
            if not axe:
                stop_script("Could not equip axe")
                return False

            # Use standard targeting sequence (never use PreTarget)
            API.UseObject(axe.Serial)
            if API.WaitForTarget(timeout=0.5):
                API.Target(log.Serial)

            API.Pause(0.5)

            if API.InJournalAny(wait_msgs):
                API.Pause(0.5)

        # Dump boards after each batch
        if not dump_boards_to_pack(state):
            # Pack might be full, check if we should deposit
            boards_in_pack = count_items(0x1BD7, state.pack_serial)
            if boards_in_pack >= 1600:
                return True  # Let caller handle deposit routine

    return True


def dump_boards_to_pack(state):
    """Dump boards to pack. Returns True if successful or pack has space."""
    dest = state.pack_serial
    if not dest:
        return False

    # Check if pack is in range first
    if not is_pack_in_range(state):
        return False

    boards_in_backpack = count_items(0x1BD7, API.Backpack)
    if boards_in_backpack <= 0:
        return True  # Nothing to dump

    existing = count_items(0x1BD7, dest)
    remaining = max(0, 1600 - existing)

    if remaining <= 0:
        return False  # Pack is full

    boards = API.FindTypeAll(0x1BD7, API.Backpack) or []
    moved_any = False

    for b in boards:
        if API.StopRequested or remaining <= 0:
            break

        amount = getattr(b, "Amount", 0) or 0
        if amount <= 0:
            continue

        move_amt = min(amount, remaining)
        if move_item_robust(b.Serial, dest, move_amt):
            remaining -= move_amt
            moved_any = True

    return moved_any or remaining > 0


def harvest_tree(state, tree):
    """Harvest a single tree until depleted or stuck."""
    px, py = API.Player.X, API.Player.Y
    dist = chebyshev_distance(px, py, tree.X, tree.Y)

    # Pathfind if needed
    if dist > 1:
        if not pathfind_to_tree(tree):
            mark_depleted(state, tree)
            return

    key = (tree.X, tree.Y)
    API.ClearJournal()

    # Harvest loop
    while not API.StopRequested:
        # Weight check - trigger deposit if pack full
        if is_heavy(buffer=60):
            warn_weight(state)
            if not chop_all_logs(state):
                # Deposit routine needed
                return
            warn_weight(state)

            # Check if pack is full
            boards_in_pack = count_items(0x1BD7, state.pack_serial)
            if boards_in_pack >= 1600:
                return  # Caller will trigger deposit

            if is_heavy(buffer=60):
                break

        # Track inventory before chop
        before_logs = count_items(0x1BDD, API.Backpack)
        before_boards = count_items(0x1BD7, API.Backpack)

        chop_tree(state, tree)
        API.Pause(0.1)

        # Track inventory after chop
        after_logs = count_items(0x1BDD, API.Backpack)
        after_boards = count_items(0x1BD7, API.Backpack)

        # Inventory-based progress detection
        progress = (after_logs > before_logs) or (after_boards > before_boards)

        # Also check journal for success messages
        if progress or API.InJournalAny(success_msgs):
            state.tree_attempts[key] = 0
        else:
            state.tree_attempts[key] = state.tree_attempts.get(key, 0) + 1

        # Check for depletion
        if API.InJournalAny(depleted_msgs):
            # Check specifically for "can't use axe" errors - flag as bad graphic
            # Use regex pattern to handle apostrophe variations (straight ' vs curly ')
            if API.InJournalAny(["$[Cc]an.t use an axe", "cannot use an axe on that"]):
                graphic = getattr(tree, "Graphic", None)
                if graphic:
                    if graphic in tree_graphics:
                        tree_graphics.remove(graphic)
                    state.bad_graphics.add(graphic)
                    save_bad_graphics(state)
                    if DEBUG:
                        API.SysMsg(
                            f"DEBUG: Bad tree graphic 0x{graphic:X} at ({tree.X}, {tree.Y}) - saved",
                            946,
                        )
            mark_depleted(state, tree)
            break

        # Check for wait message
        if API.InJournalAny(wait_msgs):
            API.Pause(0.5)

        # Give up if stuck
        if state.tree_attempts.get(key, 0) >= 6:
            API.SysMsg("No progress on tree - skipping temporarily")
            mark_depleted(state, tree)
            break


# =========================
# TRAVEL FUNCTIONS
# =========================


def cast_mark(rune_serial):
    """Cast Mark spell on a rune. Returns True if successful."""
    API.ClearJournal()
    API.CastSpell("Mark")

    if not API.WaitForTarget(timeout=5):
        API.SysMsg("Mark spell failed - no target cursor", 32)
        return False

    API.Target(rune_serial)

    # Wait for spell cast time (Mark is a longer cast, ~3.5 seconds)
    # Note: Mark spell has no success message, only a sound
    API.Pause(3.5)

    # Only fail if we see an explicit failure message
    if API.InJournalAny(TRAVEL_FAIL_MSGS):
        API.SysMsg("Mark spell failed", 32)
        return False

    API.SysMsg("Mark spell cast (assuming success)", 946)
    return True


# cast_recall() and wait_for_travel() moved to lib.runebook (use recall_and_target)

# =========================
# DEPOSIT ROUTINE
# =========================


def dump_to_chest(state):
    """Dump all boards and bonus items from backpack and pack to chest."""
    chest_serial = state.drop_chest_serial

    # All item types to drop (boards + bonus items)
    all_items = [0x1BD7] + bonus_lumberjack_items

    # Drop from backpack and pack animal
    dropped = drop_items_to_container(chest_serial, all_items, API.Backpack)
    dropped += drop_items_to_container(chest_serial, all_items, state.pack_serial)

    if dropped > 0:
        API.SysMsg(f"Dropped {dropped} item stacks", 946)


def deposit_routine(state):
    """Full deposit routine: mark location, recall home, dump, recall back."""

    # 1. Re-equip Main dress agent (for spellbook/reagents)
    API.Dress("Main")
    API.Pause(1.5)

    # 2. Verify rune exists
    rune = API.FindItem(state.rune_serial)
    if not rune:
        stop_script("Cannot find marking rune - check your backpack")
        return False

    # 3. Cast Mark on the rune (save current lumber spot)
    if not cast_mark(state.rune_serial):
        stop_script("Failed to mark rune")
        return False

    # 4. Cast Recall to runebook (go home)
    API.HeadMsg("Recalling home...", API.Player.Serial, 946)
    if not recall_and_target(state.runebook_serial):
        stop_script("Failed to recall home")
        return False

    # 5. Pathfind to drop chest
    chest = API.FindItem(state.drop_chest_serial)
    if not chest:
        stop_script("Cannot find drop chest")
        return False

    API.Pathfind(chest.X, chest.Y, chest.Z, distance=1, wait=True, timeout=10)
    API.Pause(0.5)

    # 6. Open chest and dump boards
    API.HeadMsg("Depositing...", API.Player.Serial, 946)
    API.UseObject(state.drop_chest_serial)
    API.Pause(1.0)
    dump_to_chest(state)
    API.Pause(1.5)  # Wait for server to update weight

    # 7. Cast Recall to marked rune (return to lumber spot)
    API.HeadMsg("Recalling back...", API.Player.Serial, 946)
    if not recall_and_target(state.rune_serial):
        stop_script("Failed to recall back to lumber spot")
        return False

    # Re-open pack animal backpack after teleport
    API.UseObject(state.pack_serial)
    API.Pause(1.0)

    API.HeadMsg("Deposit complete!", API.Player.Serial, 62)
    return True


# =========================
# MAIN
# =========================


def main():
    # Handle existing target cursor
    if API.HasTarget("beneficial"):
        API.Stop()
        return
    if API.HasTarget("any"):
        API.CancelTarget()

    API.SysMsg("Lumberjacking started")

    state = LumberjackState()

    # Load persisted bad graphics
    state.bad_graphics = load_bad_graphics()
    if DEBUG and state.bad_graphics:
        API.SysMsg(
            f"DEBUG: Loaded {len(state.bad_graphics)} bad graphics from storage", 946
        )

    # Check if this is first run
    first_run = is_first_run()

    # Setup all items
    if not setup_all_items(state, first_run):
        return

    # Wait for player to travel to lumber spot
    if not wait_for_travel_to_lumber_spot(state, first_run):
        return

    # Re-open pack animal backpack after travel
    API.SysMsg("Opening pack animal backpack after travel...", 946)
    API.UseObject(state.pack_serial)
    API.Pause(1.0)

    # Main loop
    while not API.StopRequested:
        # Equip axe
        axe = ensure_axe_equipped(state)
        if not axe:
            stop_script("Could not equip axe")
            break

        # Check if pack is full - trigger deposit
        boards_in_pack = count_items(0x1BD7, state.pack_serial)
        if boards_in_pack >= 1600:
            if not deposit_routine(state):
                break
            continue

        # Weight management
        if is_heavy(buffer=60):
            warn_weight(state)
            if not chop_all_logs(state):
                break
            warn_weight(state)

            # Check again if pack is full after chopping
            boards_in_pack = count_items(0x1BD7, state.pack_serial)
            if boards_in_pack >= 1600:
                if not deposit_routine(state):
                    break
                continue

            # If still heavy, wait for pack and retry dump
            if is_heavy(buffer=60):
                if not is_pack_in_range(state):
                    if not wait_for_pack(state, timeout=30):
                        API.HeadMsg("Pack still away...", API.Player.Serial, 32)
                        API.Pause(1.0)
                        continue

                # Pack is in range, try dumping again
                dump_boards_to_pack(state)

                if is_heavy(buffer=60):
                    API.Pause(0.5)
                    continue

        # Cleanup expired depletion entries
        cleanup_depleted(state)

        # Find tree
        tree = find_nearest_tree(state)
        if not tree:
            state.no_trees_count += 1
            API.SysMsg(f"No trees nearby ({state.no_trees_count}/20)")
            if state.no_trees_count >= 20:
                API.SysMsg(
                    "No trees found after 20 attempts - recalling home and stopping", 32
                )
                API.Dress("Main")
                API.Pause(1.5)
                recall_and_target(state.runebook_serial)
                break
            API.Pause(1.0)
            continue

        # Harvest tree
        harvest_tree(state, tree)
        state.no_trees_count = 0  # Reset counter after successful tree find

        # Check if pack is full after harvesting
        boards_in_pack = count_items(0x1BD7, state.pack_serial)
        if boards_in_pack >= 1600:
            if not deposit_routine(state):
                break

        API.Pause(0.1)

    # Print summary of bad graphics found
    if state.bad_graphics:
        API.SysMsg("=== Bad Tree Graphics Found ===", 32)
        graphics_list = ", ".join([f"0x{g:X}" for g in sorted(state.bad_graphics)])
        API.SysMsg(f"Remove these from tree_graphics: {graphics_list}", 32)
        API.SysMsg(f"Total bad graphics: {len(state.bad_graphics)}", 32)

    API.SysMsg("Lumberjacking finished")


main()
