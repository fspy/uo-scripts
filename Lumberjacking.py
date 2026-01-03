# pyright: reportCallIssue=false

import time
import API

# =========================
# CONFIG
# =========================

# Gargish axe graphic
AXE_GRAPHIC = 0x0F49 # 0x48B2

# Logs and boards
LOG_GRAPHIC = 0x1BDD
BOARD_GRAPHIC = 0x1BD7

# Search radius for trees (in tiles)
SCAN_RANGE = 16

# Tree tile graphics from ServUO source for reliable detection.
# If your shard uses custom tree graphics, extend this list.
TREE_TILE_GRAPHICS = [
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

# Build set for O(1) lookup
TREE_GRAPHICS = set(TREE_TILE_GRAPHICS)

# Pathfind to within this distance of the tree
PATHFIND_DISTANCE = 1

# When weight is within this many stones of max, convert logs -> boards
WEIGHT_BUFFER = 60

# Pack dump settings
PACK_DUMP_ENABLED = True
PACK_TARGET = 0  # Set at runtime via targeting
PACK_CAPACITY = 1600
MAX_PACK_FAILURES = 3

# Mark trees as "depleted" for this long (seconds)
DEPLETED_COOLDOWN = 180.0

# If we attempt the same tree this many times without success/depletion,
# mark it "depleted" temporarily to avoid getting stuck.
MAX_TREE_ATTEMPTS = 6

# Timing
ACTION_DELAY = 0.5  # pause after server actions (chop, equip, move item)
LOOP_DELAY = 0.1  # main loop pacing
JOURNAL_WINDOW = 2.0  # how far back to check journal (seconds)
MESSAGE_COOLDOWN = 5.0  # prevent message spam (warnings)

# Feature flags
USE_TARGET_RESOURCE = True  # Try API.TargetResource first (faster, server-dependent)
RUNAWAY_ON_FULL = True  # Say "[runaway" when pack full to teleport to Luna

# Journal messages that indicate chop succeeded or tree still has wood
SUCCESS_MSGS = [
    "and put them in your backpack",
    "fail to produce any useable wood",
]

# Journal messages that indicate tree depleted or unreachable
DEPLETED_MSGS = [
    "not enough wood here to harvest",
    "too far away",
    "cannot see that",
    "can't use an axe on that",
    "cannot use an axe on that",
]

# Journal messages that indicate you should pause/retry
WAIT_MSGS = [
    "you must wait",
]


# =========================
# STATE
# =========================


class LumberjackState:
    """Holds all runtime state for the lumberjacking session."""

    def __init__(self):
        self.depleted_until = {}  # (x,y) -> expiry timestamp
        self.tree_attempts = {}  # (x,y) -> attempt count
        self.last_warn_time = 0.0
        self.last_msg_time = 0.0
        self.pack_failures = 0
        self.pack_dest = 0  # resolved container serial
        self.target_resource_works = True  # disable if TargetResource fails


# =========================
# HELPERS
# =========================


def count_items(graphic, container):
    """Count total amount of items with graphic in container."""
    items = API.FindTypeAll(graphic, container) or []
    return sum(getattr(it, "Amount", 0) or 0 for it in items)


def is_heavy():
    """True if near max weight (within WEIGHT_BUFFER)."""
    p = API.Player
    if not p or p.WeightMax is None or p.Weight is None:
        return False
    return p.Weight >= p.WeightMax - WEIGHT_BUFFER


def is_overweight():
    """True if over max weight."""
    p = API.Player
    if not p or p.WeightMax is None or p.Weight is None:
        return False
    return p.Weight > p.WeightMax


def stop_script(msg):
    """Stop script with error message."""
    API.SysMsg(msg, 32)
    API.Stop()


def throttled_msg(state, msg, hue=946):
    """Send message if cooldown elapsed. Returns True if sent."""
    now = time.time()
    if now - state.last_msg_time >= MESSAGE_COOLDOWN:
        state.last_msg_time = now
        API.SysMsg(msg, hue)
        return True
    return False


def chebyshev(x1, y1, x2, y2):
    """Chebyshev distance (max of x/y deltas)."""
    return max(abs(x1 - x2), abs(y1 - y2))


def wait_for_journal(msgs, timeout):
    """Wait for any message to appear in journal. Returns True if found."""
    deadline = time.time() + timeout
    while time.time() < deadline and not API.StopRequested:
        if API.InJournalAny(msgs):
            return True
        API.Pause(0.05)
    return False


# =========================
# AXE FUNCTIONS
# =========================


def get_equipped_axe():
    """Check if axe is equipped in either hand. Returns equipped axe or None."""
    two_handed = API.FindLayer("TwoHanded")
    if two_handed and two_handed.Graphic == AXE_GRAPHIC:
        return two_handed

    one_handed = API.FindLayer("OneHanded")
    if one_handed and one_handed.Graphic == AXE_GRAPHIC:
        return one_handed

    return None


def find_axe():
    """Find axe in hands or backpack."""
    equipped = get_equipped_axe()
    if equipped:
        return equipped
    return API.FindType(AXE_GRAPHIC, API.Backpack)


def ensure_axe_equipped(axe):
    """Equip axe if not already equipped. Returns equipped axe or None."""
    if not axe:
        return None

    equipped = get_equipped_axe()
    if equipped:
        return equipped

    # Dismount if mounted
    if API.Player.Mount:
        API.Dismount(skipQueue=True)
        API.Pause(0.5)

    # Try direct equip
    API.EquipItem(axe.Serial)
    API.Pause(ACTION_DELAY)

    equipped = get_equipped_axe()
    if equipped:
        return equipped

    # Free right hand if occupied
    if API.FindLayer("TwoHanded") or API.FindLayer("OneHanded"):
        API.ClearRightHand()
        API.Pause(0.25)

    API.EquipItem(axe.Serial)
    API.Pause(ACTION_DELAY)

    return get_equipped_axe()


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
    if getattr(static, "Graphic", 0) in TREE_GRAPHICS:
        return True

    # Impassable vegetation (catches some edge cases)
    if getattr(static, "IsVegetation", False) and getattr(
        static, "IsImpassible", False
    ):
        return True

    return False


def find_nearest_tree(state):
    """Find nearest non-depleted tree within SCAN_RANGE."""
    px, py = API.Player.X, API.Player.Y
    statics = API.GetStaticsInArea(
        px - SCAN_RANGE, py - SCAN_RANGE, px + SCAN_RANGE, py + SCAN_RANGE
    )

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
    return min(trees.values(), key=lambda t: chebyshev(px, py, t.X, t.Y))


def pathfind_to_tree(tree):
    """Pathfind to tree. Returns True if successful."""
    return API.Pathfind(
        tree.X, tree.Y, tree.Z, distance=PATHFIND_DISTANCE, wait=True, timeout=10
    )


def mark_depleted(state, tree):
    """Mark tree as depleted for DEPLETED_COOLDOWN seconds."""
    key = (tree.X, tree.Y)
    state.depleted_until[key] = time.time() + DEPLETED_COOLDOWN
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
# PACK DUMP FUNCTIONS
# =========================


def resolve_pack_dest(serial):
    """Resolve pack destination serial. Returns container serial or 0."""
    if not serial:
        return 0

    # Check if it's a container item
    item = API.FindItem(serial)
    if item and getattr(item, "IsContainer", False):
        return item.Serial

    # Check if it's a mobile with a backpack
    mob = API.FindMobile(serial)
    if mob and getattr(mob, "Backpack", None):
        return mob.Backpack.Serial

    return 0


def setup_pack_dest():
    """Setup pack destination. Returns container serial or 0."""
    if PACK_TARGET:
        dest = resolve_pack_dest(PACK_TARGET)
        if dest:
            return dest

    API.SysMsg("Target pack animal or its backpack", 32)
    target = API.RequestTarget(timeout=15.0)
    if not target:
        return 0

    dest = resolve_pack_dest(target)
    if dest:
        API.SysMsg(f"Pack destination: 0x{dest:X}")
        return dest
    else:
        API.SysMsg("Invalid pack target (not a container or mobile with backpack)", 32)
        return 0


def dump_boards_to_pack(state):
    """Dump boards to pack. Returns True if successful or pack has space."""
    dest = state.pack_dest
    if not dest:
        throttled_msg(state, "Pack dump enabled but no valid destination", 32)
        return False

    boards_in_backpack = count_items(BOARD_GRAPHIC, API.Backpack)
    if boards_in_backpack <= 0:
        return True  # Nothing to dump

    existing = count_items(BOARD_GRAPHIC, dest)
    remaining = max(0, PACK_CAPACITY - existing)

    if remaining <= 0:
        throttled_msg(state, f"Pack full ({existing}/{PACK_CAPACITY} boards)", 32)
        return False  # Pack is full

    boards = API.FindTypeAll(BOARD_GRAPHIC, API.Backpack) or []
    moved_any = False

    for b in boards:
        if API.StopRequested or remaining <= 0:
            break

        amount = getattr(b, "Amount", 0) or 0
        if amount <= 0:
            continue

        move_amt = min(amount, remaining)
        API.MoveItem(b.Serial, dest, amt=move_amt)
        API.Pause(ACTION_DELAY)
        remaining -= move_amt
        moved_any = True

    if not moved_any:
        throttled_msg(state, "Failed to move boards to pack (is it nearby?)", 32)
        return False

    return remaining > 0  # True if pack still has space


def handle_full_pack():
    """Handle full pack scenario. Returns False to stop script."""
    if RUNAWAY_ON_FULL:
        API.SysMsg("Pack full! Running away to safety...", 32)
        API.Msg("[runaway")
        API.Pause(2.0)
    stop_script("Pack animal full - cannot continue")
    return False


# =========================
# CHOPPING FUNCTIONS
# =========================


def chop_tree(state, axe, tree):
    """Chop a tree. Returns True if action was sent."""
    axe = ensure_axe_equipped(axe)
    if not axe:
        stop_script("Could not equip axe")
        return False

    # If we're already holding a target cursor, just retarget
    if API.HasTarget("any"):
        API.Target(tree.X, tree.Y, tree.Z, tree.Graphic)
        wait_for_journal(SUCCESS_MSGS + DEPLETED_MSGS + WAIT_MSGS, ACTION_DELAY)
        return True

    # Try TargetResource if enabled (server-dependent feature)
    if USE_TARGET_RESOURCE and state.target_resource_works:
        API.TargetResource(axe.Serial, 2)  # 2 = wood
        API.Pause(ACTION_DELAY)

        # Check if it worked
        if API.InJournalAny(SUCCESS_MSGS + DEPLETED_MSGS):
            return True

        # TargetResource didn't work - disable and fall through to manual
        state.target_resource_works = False
        API.SysMsg("TargetResource not supported - using manual targeting")

    # Manual targeting
    API.UseObject(axe.Serial)

    if API.WaitForTarget(timeout=0.75) or API.HasTarget("any"):
        API.Target(tree.X, tree.Y, tree.Z, tree.Graphic)

    wait_for_journal(SUCCESS_MSGS + DEPLETED_MSGS + WAIT_MSGS, ACTION_DELAY)
    return True


def chop_all_logs(state, axe):
    """Convert all logs to boards. Returns True if successful."""
    while not API.StopRequested:
        logs = API.FindTypeAll(LOG_GRAPHIC, API.Backpack) or []
        if not logs:
            break

        for log in logs:
            if API.StopRequested:
                return False

            API.ClearJournal()

            axe = ensure_axe_equipped(axe)
            if not axe:
                stop_script("Could not equip axe")
                return False

            # PreTarget to avoid targeting ground/tile
            API.PreTarget(log.Serial)
            API.UseObject(axe.Serial)

            # Cancel if target cursor appears (pretarget didn't apply)
            if API.WaitForTarget(timeout=0.25):
                API.CancelTarget()

            API.Pause(ACTION_DELAY)
            API.CancelPreTarget()

            if API.InJournalAny(WAIT_MSGS):
                API.Pause(ACTION_DELAY)

        # Dump boards after each batch
        if PACK_DUMP_ENABLED:
            if not dump_boards_to_pack(state):
                state.pack_failures += 1
                if state.pack_failures >= MAX_PACK_FAILURES:
                    # Pack is full - check if still heavy
                    if is_heavy():
                        return handle_full_pack()
            else:
                state.pack_failures = 0
    
    # Final dump attempt after all logs processed
    if PACK_DUMP_ENABLED and state.pack_dest:
        if not dump_boards_to_pack(state):
            state.pack_failures += 1
            if state.pack_failures >= MAX_PACK_FAILURES and is_heavy():
                return handle_full_pack()
        else:
            state.pack_failures = 0

    return True


def harvest_tree(state, axe, tree):
    """Harvest a single tree until depleted or stuck."""
    px, py = API.Player.X, API.Player.Y
    dist = chebyshev(px, py, tree.X, tree.Y)

    # Pathfind if needed
    if dist > PATHFIND_DISTANCE:
        if not pathfind_to_tree(tree):
            mark_depleted(state, tree)
            return

    key = (tree.X, tree.Y)
    API.ClearJournal()

    # Harvest loop
    while not API.StopRequested:
        # Weight check
        if is_heavy():
            warn_weight(state)
            if not chop_all_logs(state, axe):
                return  # Pack full, already handled
            warn_weight(state)
            if is_heavy():
                break

        # Track inventory before chop
        before_logs = count_items(LOG_GRAPHIC, API.Backpack)
        before_boards = count_items(BOARD_GRAPHIC, API.Backpack)

        chop_tree(state, axe, tree)
        API.Pause(LOOP_DELAY)

        # Track inventory after chop
        after_logs = count_items(LOG_GRAPHIC, API.Backpack)
        after_boards = count_items(BOARD_GRAPHIC, API.Backpack)

        # Inventory-based progress detection
        progress = (after_logs > before_logs) or (after_boards > before_boards)

        # Also check journal for success messages
        if progress or API.InJournalAny(SUCCESS_MSGS):
            state.tree_attempts[key] = 0
        else:
            state.tree_attempts[key] = state.tree_attempts.get(key, 0) + 1

        # Check for depletion
        if API.InJournalAny(DEPLETED_MSGS):
            mark_depleted(state, tree)
            break

        # Check for wait message
        if API.InJournalAny(WAIT_MSGS):
            API.Pause(ACTION_DELAY)

        # Give up if stuck
        if state.tree_attempts.get(key, 0) >= MAX_TREE_ATTEMPTS:
            API.SysMsg("No progress on tree - skipping temporarily")
            mark_depleted(state, tree)
            break


# =========================
# WARNING FUNCTIONS
# =========================


def warn_weight(state):
    """Warn player about weight status (throttled)."""
    if not is_heavy():
        return

    now = time.time()
    if now - state.last_warn_time < MESSAGE_COOLDOWN:
        return

    state.last_warn_time = now

    if is_overweight():
        API.SysMsg(
            f"OVERWEIGHT: Can't move ({API.Player.Weight}/{API.Player.WeightMax})", 32
        )
        API.Msg("OVERWEIGHT: Can't move")
    else:
        API.SysMsg(
            f"WARNING: Near weight limit ({API.Player.Weight}/{API.Player.WeightMax})",
            32,
        )
        API.Msg("Overweight warning!")


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

    # Setup pack dump
    if PACK_DUMP_ENABLED:
        state.pack_dest = setup_pack_dest()
        if state.pack_dest:
            API.SysMsg(f"Pack dump enabled: 0x{state.pack_dest:X}")
        else:
            API.SysMsg("Pack dump disabled - no valid target", 32)

    # Main loop
    while not API.StopRequested:
        # Find and equip axe
        axe = find_axe()
        if not axe:
            stop_script(f"No axe found (graphic 0x{AXE_GRAPHIC:X})")
            break

        axe = ensure_axe_equipped(axe)
        if not axe:
            stop_script("Could not equip axe")
            break

        # Weight management
        if is_heavy():
            warn_weight(state)
            if not chop_all_logs(state, axe):
                break  # Pack full, already handled
            warn_weight(state)
            if is_heavy():
                API.Pause(LOOP_DELAY)
                continue

        # Cleanup expired depletion entries
        cleanup_depleted(state)

        # Find tree
        tree = find_nearest_tree(state)
        if not tree:
            API.SysMsg("No trees nearby")
            API.Pause(1.0)
            continue

        # Harvest tree
        harvest_tree(state, axe, tree)
        API.Pause(LOOP_DELAY)

    API.SysMsg("Lumberjacking finished")


main()
