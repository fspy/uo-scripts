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

# Search radius for trees (in tiles)
TREE_SCAN_RANGE = 12

# Pathfind to within this distance of the tree
PATHFIND_DISTANCE = 1

# When weight is within this many stones of max, convert logs -> boards
WEIGHT_BUFFER = 30

# If still within this many stones after converting logs, warn
WARN_BUFFER = 10
WARN_COOLDOWN_SECONDS = 10.0

# Mark trees as "depleted" for this long (seconds)
DEPLETED_TTL_SECONDS = 180.0

# After targeting a tree, watch recent journal output for results.
# Some shards send the "no wood" message late; using a short time window is
# more reliable than clearing the journal and hoping we read it in time.
CHOP_RESULT_WINDOW = 3.0
CHOP_RESULT_TIMEOUT = 1.5
CHOP_RESULT_POLL = 0.1

# If we attempt the same tree this many times without success/depletion,
# mark it "depleted" temporarily to avoid getting stuck.
MAX_ATTEMPTS_PER_TREE = 6

# Delays
CHOP_DELAY = 0.65
EQUIP_DELAY = 0.6
LOOP_DELAY = 0.25

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


def find_trees(scan_range: int) -> list:
    px, py = int(API.Player.X), int(API.Player.Y)
    statics = API.GetStaticsInArea(
        px - scan_range, py - scan_range, px + scan_range, py + scan_range
    )

    if not statics:
        return []

    trees = []
    for s in statics:
        if not getattr(s, "IsTree", False):
            continue

        if hasattr(s, "HasLineOfSightFrom") and not s.HasLineOfSightFrom():
            continue

        trees.append(s)

    return trees


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

    # Don't rely on ClearJournal() here; journal entries can arrive late.
    API.UseObject(int(axe.Serial))

    if not API.WaitForTarget(timeout=5):
        return False

    API.Target(int(tree.X), int(tree.Y), int(tree.Z), int(tree.Graphic))
    API.Pause(CHOP_DELAY)
    return True


def _journal_has_any_recent(substrings: list[str], seconds: float) -> bool:
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
        if _journal_has_any_recent(DEPLETED_MSGS, CHOP_RESULT_WINDOW) or _journal_has_any_recent(
            WAIT_MSGS, CHOP_RESULT_WINDOW
        ):
            return
        API.Pause(CHOP_RESULT_POLL)


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


def warn_if_still_heavy(last_warn: float) -> float:
    if not is_near_max(WARN_BUFFER):
        return last_warn

    now = time.time()
    if now - last_warn < WARN_COOLDOWN_SECONDS:
        return last_warn

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

    chop_tree(axe, tree)

    # Wait for delayed server messages so we don't miss depletion.
    wait_for_chop_result()

    key = (int(tree.X), int(tree.Y))
    tree_attempts[key] = tree_attempts.get(key, 0) + 1

    if _journal_has_any_recent(DEPLETED_MSGS, CHOP_RESULT_WINDOW):
        depleted_until[key] = time.time() + DEPLETED_TTL_SECONDS
        tree_attempts.pop(key, None)
    elif _journal_has_any_recent(WAIT_MSGS, CHOP_RESULT_WINDOW):
        API.Pause(0.5)
    elif tree_attempts[key] >= MAX_ATTEMPTS_PER_TREE:
        API.SysMsg("No progress on this tree; skipping temporarily")
        depleted_until[key] = time.time() + DEPLETED_TTL_SECONDS
        tree_attempts.pop(key, None)

    API.Pause(LOOP_DELAY)

API.SysMsg("Lumberjacking script finished")
