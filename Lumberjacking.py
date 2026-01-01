# pyright: reportCallIssue=false

import time
import API

# =========================
# CONFIG
# =========================

# Gargish axe graphic
AXE_TYPE = 0x48B2

# Logs
LOG_TYPE = 0x1BDD

# Boards (result from chopping logs)
BOARD_TYPE = 0x1BD7

# Search radius for trees (in tiles)
TREE_SCAN_RANGE = 12

# Tree detection behavior
INCLUDE_VEGETATION = True
USE_NAME_FALLBACK = True
FILTER_LINE_OF_SIGHT = False
DEBUG_TREE_COUNTS = False

# Prefer explicit graphics list (from ServUO tile tables) for conservative detection.
# If your shard uses custom tree graphics, extend this list.
USE_TREE_GRAPHIC_LIST = True
TREE_TILE_GRAPHICS = set(
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

# Fallback keywords for shards where tree statics aren't flagged as IsTree.
# Kept conservative by also requiring impassible for non-IsTree matches.
TREE_NAME_KEYWORDS = [
    "tree",
    "oak",
    "pine",
    "yew",
    "willow",
    "cedar",
    "cypress",
]

# Prevent DEBUG_TREE_COUNTS from spamming every loop.
TREE_DEBUG_COOLDOWN_SECONDS = 5.0

# Pathfind to within this distance of the tree
PATHFIND_DISTANCE = 1

# When weight is within this many stones of max, convert logs -> boards
WEIGHT_BUFFER = 30

# Optional: dump boards into a pack animal/container when heavy.
# Set PACK_DESTINATION_SERIAL to the pack animal (mobile) OR its backpack (container item).
USE_PACK_DUMP = False
PACK_DESTINATION_SERIAL = 0
PACK_DUMP_DISTANCE = 2
PACK_DUMP_PAUSE = 0.7

# If USE_PACK_DUMP is enabled but no destination is set, prompt on start.
PACK_PROMPT_TIMEOUT = 15.0

# If still within this many stones after converting logs, warn
WARN_BUFFER = 10
WARN_COOLDOWN_SECONDS = 10.0

# Mark trees as "depleted" for this long (seconds)
DEPLETED_TTL_SECONDS = 180.0

# After targeting a tree, we *optionally* scan journal output for "depleted".
# Prefer inventory-based detection for speed/reliability; journal is fallback.
CHOP_RESULT_WINDOW = 1.0
CHOP_RESULT_TIMEOUT = 0.35
CHOP_RESULT_POLL = 0.05

# If we attempt the same tree this many times without success/depletion,
# mark it "depleted" temporarily to avoid getting stuck.
MAX_ATTEMPTS_PER_TREE = 6

# Delays
CHOP_DELAY = 0.45
EQUIP_DELAY = 0.4
LOOP_DELAY = 0.1

# After each chop, give the backpack a moment to update.
POST_CHOP_CHECK_DELAY = 0.1

# Journal messages that indicate no wood / out of range / invalid target.
# Keep these as *substrings* (we match case-insensitive against recent journal entries).
DEPLETED_MSGS = [
    "no wood",
    "not enough wood",
    "too far away",
    "cannot see that",
    "can't use an axe on that",
    "cannot use an axe on that",
    "there is no wood",
]

# Journal messages that indicate you should pause/retry.
WAIT_MSGS = [
    "you must wait",
]


def is_near_max(buffer: int) -> bool:
    if not API.Player or API.Player.WeightMax is None or API.Player.Weight is None:
        return False
    return API.Player.Weight >= (API.Player.WeightMax - buffer)


def is_overweight() -> bool:
    if not API.Player or API.Player.WeightMax is None or API.Player.Weight is None:
        return False
    return API.Player.Weight > API.Player.WeightMax


def chebyshev_dist(x1: int, y1: int, x2: int, y2: int) -> int:
    return max(abs(x1 - x2), abs(y1 - y2))


def find_axe():
    two_handed = API.FindLayer("TwoHanded")
    if two_handed and two_handed.Graphic == AXE_TYPE:
        return two_handed

    one_handed = API.FindLayer("OneHanded")
    if one_handed and one_handed.Graphic == AXE_TYPE:
        return one_handed

    return API.FindType(AXE_TYPE, API.Backpack)


def ensure_axe_equipped(axe):
    if not axe:
        return None

    two_handed = API.FindLayer("TwoHanded")
    if two_handed and two_handed.Graphic == AXE_TYPE:
        return two_handed

    one_handed = API.FindLayer("OneHanded")
    if one_handed and one_handed.Graphic == AXE_TYPE:
        return one_handed

    if API.Player.Mount:
        API.Dismount(skipQueue=True)
        API.Pause(0.5)

    # Try a straight equip first.
    API.EquipItem(int(axe.Serial))
    API.Pause(EQUIP_DELAY)

    two_handed = API.FindLayer("TwoHanded")
    if two_handed and two_handed.Graphic == AXE_TYPE:
        return two_handed

    one_handed = API.FindLayer("OneHanded")
    if one_handed and one_handed.Graphic == AXE_TYPE:
        return one_handed

    # If hands are occupied, free the right hand slot and retry.
    if API.FindLayer("TwoHanded") or API.FindLayer("OneHanded"):
        API.ClearRightHand()
        API.Pause(0.25)

    API.EquipItem(int(axe.Serial))
    API.Pause(EQUIP_DELAY)

    two_handed = API.FindLayer("TwoHanded")
    if two_handed and two_handed.Graphic == AXE_TYPE:
        return two_handed

    one_handed = API.FindLayer("OneHanded")
    if one_handed and one_handed.Graphic == AXE_TYPE:
        return one_handed

    return None


_last_tree_debug_time = 0.0


def _name_matches_tree(static) -> bool:
    name = str(getattr(static, "Name", "") or "").lower()
    if not name:
        return False
    for kw in TREE_NAME_KEYWORDS:
        if kw in name:
            return True
    return False


def _graphic_matches_tree(static) -> bool:
    if not USE_TREE_GRAPHIC_LIST:
        return False
    graphic = int(getattr(static, "Graphic", 0) or 0)
    return graphic in TREE_TILE_GRAPHICS


def find_trees(scan_range: int) -> list:
    global _last_tree_debug_time

    px, py = int(API.Player.X), int(API.Player.Y)
    statics = API.GetStaticsInArea(
        px - scan_range, py - scan_range, px + scan_range, py + scan_range
    )

    if not statics:
        return []

    # Summary counts (optional)
    total = 0
    included = 0
    is_tree_count = 0
    veg_count = 0
    name_count = 0
    los_excluded = 0

    # De-dup by (x,y). Trees often have multiple statics at the same tile
    # (trunk + canopy). Prefer the Z closest to the player so we target/pathfind
    # to the trunk instead of a high canopy component.
    by_xy = {}

    for s in statics:
        total += 1

        if getattr(s, "IsDestroyed", False):
            continue

        is_tree = bool(getattr(s, "IsTree", False))
        is_veg = bool(getattr(s, "IsVegetation", False))
        graphic_match = _graphic_matches_tree(s)
        name_match = _name_matches_tree(s) if USE_NAME_FALLBACK else False

        if is_tree or graphic_match:
            is_tree_count += 1
        if is_veg:
            veg_count += 1
        if name_match:
            name_count += 1

        # Conservative inclusion:
        # - Always include IsTree or known tree graphics
        # - Otherwise include vegetation/name matches ONLY when impassible
        #   (reduces grabbing flowers/grass that can't be chopped).
        is_impassible = bool(getattr(s, "IsImpassible", False))
        include = False
        if is_tree or graphic_match:
            include = True
        else:
            if INCLUDE_VEGETATION and is_veg and is_impassible:
                include = True
            elif USE_NAME_FALLBACK and name_match and is_impassible:
                include = True

        if not include:
            continue

        if (
            FILTER_LINE_OF_SIGHT
            and hasattr(s, "HasLineOfSightFrom")
            and not s.HasLineOfSightFrom()
        ):
            los_excluded += 1
            continue

        included += 1

        key = (int(s.X), int(s.Y))
        existing = by_xy.get(key)
        if existing is None:
            by_xy[key] = s
        else:
            existing_z = int(getattr(existing, "Z", 0) or 0)
            z = int(getattr(s, "Z", 0) or 0)

            # Keep the candidate closest to player Z.
            player_z = int(getattr(API.Player, "Z", 0) or 0)
            if abs(z - player_z) < abs(existing_z - player_z):
                by_xy[key] = s

    if DEBUG_TREE_COUNTS:
        now = time.time()
        if now - _last_tree_debug_time >= TREE_DEBUG_COOLDOWN_SECONDS:
            _last_tree_debug_time = now
            API.SysMsg(
                f"TreeScan: total={total} included={len(by_xy)} treeish={is_tree_count} veg={veg_count} name={name_count} los_excl={los_excluded}"
            )

    return list(by_xy.values())


def nearest_tree(scan_range: int, depleted_until: dict):
    now = time.time()
    px, py = int(API.Player.X), int(API.Player.Y)

    trees = find_trees(scan_range)
    if not trees:
        return None

    # Filter depleted
    available = []
    for t in trees:
        key = (int(t.X), int(t.Y))
        until = depleted_until.get(key, 0.0)
        if until > now:
            continue
        available.append(t)

    if not available:
        return None

    available.sort(key=lambda t: chebyshev_dist(px, py, int(t.X), int(t.Y)))
    return available[0]


def pathfind_to_tree(tree) -> bool:
    return API.Pathfind(
        int(tree.X),
        int(tree.Y),
        int(tree.Z),
        distance=PATHFIND_DISTANCE,
        wait=True,
        timeout=10,
    )


def chop_tree(axe, tree) -> bool:
    axe = ensure_axe_equipped(axe)
    if not axe:
        API.SysMsg("Could not equip axe; stopping", 32)
        API.Stop()
        return False

    # Some servers/clients will re-use the last target after the first chop,
    # meaning no target cursor appears on subsequent swings. Handle both cases.
    API.UseObject(int(axe.Serial))

    if API.WaitForTarget(timeout=0.75):
        API.Target(int(tree.X), int(tree.Y), int(tree.Z), int(tree.Graphic))

    API.Pause(CHOP_DELAY)
    return True


def _journal_has_any_recent(substrings, seconds) -> bool:
    entries = API.GetJournalEntries(seconds) or []
    for entry in entries:
        text = str(getattr(entry, "Text", "") or "").lower()
        for sub in substrings:
            if sub in text:
                return True
    return False


def wait_for_chop_result() -> None:
    """Wait briefly for any chopping-related journal output."""
    deadline = time.time() + CHOP_RESULT_TIMEOUT
    while time.time() < deadline and not API.StopRequested:
        if _journal_has_any_recent(
            DEPLETED_MSGS, CHOP_RESULT_WINDOW
        ) or _journal_has_any_recent(WAIT_MSGS, CHOP_RESULT_WINDOW):
            return
        API.Pause(CHOP_RESULT_POLL)


def _resolve_pack_destination() -> int:
    """Return container serial to drop boards into, or 0 if unavailable."""
    if not USE_PACK_DUMP or not PACK_DESTINATION_SERIAL:
        return 0

    # PACK_DESTINATION_SERIAL may be either:
    # - the pack animal backpack item serial (container)
    # - or the pack animal mobile serial (which exposes .Backpack)
    item = API.FindItem(int(PACK_DESTINATION_SERIAL))
    if item:
        if getattr(item, "IsContainer", False):
            return int(item.Serial)
        return 0

    mob = API.FindMobile(int(PACK_DESTINATION_SERIAL))
    if mob and getattr(mob, "Backpack", None):
        return int(mob.Backpack.Serial)

    return 0


def dump_boards_to_pack() -> None:
    dest = _resolve_pack_destination()
    if not dest:
        return

    boards = API.FindTypeAll(BOARD_TYPE, API.Backpack) or []
    if not boards:
        return

    # Moves can fail if the follower is too far away; keep it conservative.
    for b in boards:
        if API.StopRequested:
            return
        API.MoveItem(int(b.Serial), int(dest))
        API.Pause(PACK_DUMP_PAUSE)


def board_amount_in_pack() -> int:
    items = API.FindTypeAll(BOARD_TYPE, API.Backpack) or []
    total = 0
    for it in items:
        total += int(getattr(it, "Amount", 0) or 0)
    return total


def log_amount_in_pack() -> int:
    items = API.FindTypeAll(LOG_TYPE, API.Backpack) or []
    total = 0
    for it in items:
        total += int(getattr(it, "Amount", 0) or 0)
    return total


def chop_all_logs_in_pack(axe) -> None:
    while not API.StopRequested:
        logs = API.FindTypeAll(LOG_TYPE, API.Backpack) or []
        if not logs:
            return

        for log in logs:
            if API.StopRequested:
                return

            API.ClearJournal()

            # PreTarget to avoid targeting the ground/tile by mistake.
            axe = ensure_axe_equipped(axe)
            if not axe:
                API.SysMsg("Could not equip axe; stopping", 32)
                API.Stop()
                return

            API.PreTarget(int(log.Serial))
            API.UseObject(int(axe.Serial))

            # If a target cursor still appears, pretarget didn't apply; cancel so we don't hang.
            if API.WaitForTarget(timeout=0.25):
                API.CancelTarget()

            API.Pause(CHOP_DELAY)
            API.CancelPreTarget()

            if API.InJournalAny(WAIT_MSGS):
                API.Pause(0.5)

        # After converting a batch of logs, dump boards if enabled.
        if USE_PACK_DUMP:
            dump_boards_to_pack()


def warn_if_still_heavy(last_warn: float) -> float:
    if not is_near_max(WARN_BUFFER):
        return last_warn

    now = time.time()
    if now - last_warn < WARN_COOLDOWN_SECONDS:
        return last_warn

    if is_overweight():
        API.SysMsg(
            f"OVERWEIGHT: Can't move ({API.Player.Weight}/{API.Player.WeightMax}). Drop items or convert logs.",
            32,
        )
        API.Msg("OVERWEIGHT: Can't move")
    else:
        API.SysMsg(
            f"WARNING: Near weight limit ({API.Player.Weight}/{API.Player.WeightMax})",
            32,
        )
        API.Msg("Overweight warning!")

    return now


# =========================
# MAIN
# =========================

if API.HasTarget("beneficial"):
    API.Stop()
elif API.HasTarget("any"):
    API.CancelTarget()

API.SysMsg("Lumberjacking started (tree scan + pathfind)")

if USE_PACK_DUMP and not PACK_DESTINATION_SERIAL:
    API.SysMsg("Target your pack animal (or its backpack) to dump boards", 32)
    PACK_DESTINATION_SERIAL = int(API.RequestTarget(timeout=PACK_PROMPT_TIMEOUT) or 0)
    if PACK_DESTINATION_SERIAL:
        API.SysMsg(f"Pack dump target set: 0x{PACK_DESTINATION_SERIAL:X}")
        resolved = _resolve_pack_destination()
        if resolved:
            API.SysMsg(f"Pack dump container: 0x{resolved:X}")
        else:
            API.SysMsg("Pack dump target could not be resolved; pack dump disabled", 32)
            PACK_DESTINATION_SERIAL = 0
            USE_PACK_DUMP = False
    else:
        API.SysMsg("No pack dump target set; continuing without pack dump", 32)
        USE_PACK_DUMP = False

# Map of (x,y) -> time() until which we ignore it
# Used for depleted/unreachable trees.
depleted_until = {}

# Map of (x,y) -> attempt count (to avoid getting stuck if journal matching fails).
tree_attempts = {}

last_warn_time = 0.0


while not API.StopRequested:
    axe = find_axe()
    if not axe:
        API.SysMsg("No gargish axe (0x48B2) found; stopping", 32)
        break

    axe = ensure_axe_equipped(axe)
    if not axe:
        API.SysMsg("Could not equip gargish axe; stopping", 32)
        break

    if is_near_max(WEIGHT_BUFFER):
        # When overweight, pathfinding won't happen; make it obvious.
        last_warn_time = warn_if_still_heavy(last_warn_time)

        # Try to recover by converting logs -> boards.
        chop_all_logs_in_pack(axe)
        last_warn_time = warn_if_still_heavy(last_warn_time)

        API.Pause(LOOP_DELAY)
        continue

    # Clean up expired entries
    now = time.time()
    expired = [k for k, until in depleted_until.items() if until <= now]
    for k in expired:
        depleted_until.pop(k, None)
        tree_attempts.pop(k, None)

    tree = nearest_tree(TREE_SCAN_RANGE, depleted_until)
    if not tree:
        API.SysMsg("No available trees nearby")
        API.Pause(1.0)
        continue

    px, py = int(API.Player.X), int(API.Player.Y)
    dist = chebyshev_dist(px, py, int(tree.X), int(tree.Y))

    if dist > PATHFIND_DISTANCE:
        if not pathfind_to_tree(tree):
            depleted_until[(int(tree.X), int(tree.Y))] = now + DEPLETED_TTL_SECONDS
            API.Pause(LOOP_DELAY)
            continue

    key = (int(tree.X), int(tree.Y))

    # Harvest this tree until depleted.
    # We still keep the attempt safeguard in case journal detection fails.
    while not API.StopRequested:
        if is_near_max(WEIGHT_BUFFER):
            last_warn_time = warn_if_still_heavy(last_warn_time)
            chop_all_logs_in_pack(axe)
            last_warn_time = warn_if_still_heavy(last_warn_time)
            break

        before_logs = log_amount_in_pack()
        before_boards = board_amount_in_pack()

        chop_tree(axe, tree)
        API.Pause(POST_CHOP_CHECK_DELAY)

        after_logs = log_amount_in_pack()
        after_boards = board_amount_in_pack()

        # Inventory-based progress detection is fast and reliable.
        progress = (after_logs > before_logs) or (after_boards > before_boards)

        if progress:
            tree_attempts[key] = 0
        else:
            # Only do a very short journal wait if we didn't detect progress.
            wait_for_chop_result()
            tree_attempts[key] = tree_attempts.get(key, 0) + 1

        if _journal_has_any_recent(DEPLETED_MSGS, CHOP_RESULT_WINDOW):
            depleted_until[key] = time.time() + DEPLETED_TTL_SECONDS
            tree_attempts.pop(key, None)
            break

        if _journal_has_any_recent(WAIT_MSGS, CHOP_RESULT_WINDOW):
            API.Pause(0.25)

        if tree_attempts.get(key, 0) >= MAX_ATTEMPTS_PER_TREE:
            API.SysMsg("No progress on this tree; skipping temporarily")
            depleted_until[key] = time.time() + DEPLETED_TTL_SECONDS
            tree_attempts.pop(key, None)
            break

        API.Pause(LOOP_DELAY)

    API.Pause(LOOP_DELAY)

API.SysMsg("Lumberjacking script finished")
