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

# Delays
CHOP_DELAY = 0.65
EQUIP_DELAY = 0.6
LOOP_DELAY = 0.25

# Journal messages that indicate no wood / out of range / invalid target
DEPLETED_MSGS = [
    "There is no wood here to harvest.",
    "There is not enough wood here to harvest.",
    "You cannot see that.",
    "That is too far away.",
    "You can't use an axe on that.",
]

# Journal messages that indicate you should pause/retry
WAIT_MSGS = [
    "You must wait",
]


def is_near_max(buffer: int) -> bool:
    if not API.Player or API.Player.WeightMax is None or API.Player.Weight is None:
        return False
    return API.Player.Weight >= (API.Player.WeightMax - buffer)


def chebyshev_dist(x1: int, y1: int, x2: int, y2: int) -> int:
    return max(abs(x1 - x2), abs(y1 - y2))


def find_axe():
    right = API.FindLayer("RightHand")
    if right and right.Graphic == AXE_TYPE:
        return right

    left = API.FindLayer("LeftHand")
    if left and left.Graphic == AXE_TYPE:
        return left

    return API.FindType(AXE_TYPE, API.Backpack)


def ensure_axe_equipped(axe):
    if not axe:
        return None

    right = API.FindLayer("RightHand")
    if right and right.Graphic == AXE_TYPE:
        return right

    left = API.FindLayer("LeftHand")
    if left and left.Graphic == AXE_TYPE:
        return left

    if API.Player.Mount:
        API.Dismount(skipQueue=True)
        API.Pause(0.5)

    cleared = False

    right = API.FindLayer("RightHand")
    if right:
        API.ClearRightHand()
        cleared = True

    left = API.FindLayer("LeftHand")
    if left:
        API.ClearLeftHand()
        cleared = True

    if cleared:
        API.Pause(0.25)

    API.EquipItem(int(axe.Serial))
    API.Pause(EQUIP_DELAY)

    right = API.FindLayer("RightHand")
    if right and right.Graphic == AXE_TYPE:
        return right

    left = API.FindLayer("LeftHand")
    if left and left.Graphic == AXE_TYPE:
        return left

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

    API.ClearJournal()
    API.UseObject(int(axe.Serial))

    if not API.WaitForTarget(timeout=5):
        return False

    API.Target(int(tree.X), int(tree.Y), int(tree.Z), int(tree.Graphic))
    API.Pause(CHOP_DELAY)
    return True


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
# Used for depleted and unreachable trees.
depleted_until = {}
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

    if API.InJournalAny(DEPLETED_MSGS, clearMatches=True):
        depleted_until[(int(tree.X), int(tree.Y))] = time.time() + DEPLETED_TTL_SECONDS
    elif API.InJournalAny(WAIT_MSGS, clearMatches=True):
        API.Pause(0.5)

    API.Pause(LOOP_DELAY)

API.SysMsg("Lumberjacking script finished")
