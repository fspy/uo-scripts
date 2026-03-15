# pyright: reportCallIssue=false
import time

import API
from _lib.items import drop_all_items_at_home, move_item_robust
from _lib.persistence import load_int, load_json, save_int, save_json, setup_target
from _lib.recovery import Recovery
from _lib.runebook import TRAVEL_FAIL_MSGS, recall_with_retry
from _lib.utils import (
    chebyshev_distance,
    count_items,
    dismount_if_mounted,
    stop_script,
    use_item_on_target,
)
from _lib.weight import is_heavy

MAX_TRAVEL_RETRIES = 3
TRAVEL_RETRY_DELAY = 2.0
USE_SACRED_JOURNEY = False
MAX_CONSECUTIVE_FAILURES = 5

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

success_msgs = ["and put them in your backpack", "fail to produce any useable wood"]

depleted_msgs = [
    "not enough wood here to harvest",
    "too far away",
    "cannot see that",
    "can't use an axe on that",
    "cannot use an axe on that",
]

wait_msgs = ["you must wait"]


class LumberjackState:
    def __init__(self):
        self.depleted_until = {}
        self.tree_attempts = {}
        self.no_trees_count = 0

        self.axe_serial = 0
        self.pack_serial = 0
        self.runebook_serial = 0
        self.drop_chest_serial = 0
        self.rune_serial = 0

        self.bad_graphics = set()

        self.consecutive_failures = 0


def wait_for_any(messages: list, timeout: float) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline and not API.StopRequested:
        if API.InJournalAny(messages):
            return True
        API.Pause(0.05)
    return False


def is_pack_in_range(state):
    if not state.pack_serial:
        return False

    pack = API.FindItem(state.pack_serial)
    return pack is not None and pack.Distance <= 2


def wait_for_pack(state, timeout=30):
    if is_pack_in_range(state):
        return True

    deadline = time.time() + timeout
    while time.time() < deadline and not API.StopRequested:
        if is_pack_in_range(state):
            return True
        API.Pause(1.0)

    return False


def load_bad_graphics():
    data = load_json("LumberjackBadGraphics", default=[])
    return set(data) if isinstance(data, list) else set()


def save_bad_graphics(state):
    if not state.bad_graphics:
        return

    save_json("LumberjackBadGraphics", sorted(list(state.bad_graphics)))


def setup_drop_chest(first_run):
    return setup_target(
        "LumberjackDropChest", "Target drop chest at home", verify_in_range=first_run
    )


def setup_all_items(state, first_run):
    if first_run:
        API.SysMsg("First run detected - please target all items at home", 946)

    state.axe_serial = setup_target("LumberjackAxe", "Target your axe")
    if not state.axe_serial:
        stop_script("Axe setup failed")
        return False

    state.pack_serial = setup_target("LumberjackPack", "Target pack animal")
    if not state.pack_serial:
        stop_script("Pack animal setup failed")
        return False

    mob = API.FindMobile(state.pack_serial)
    if mob and getattr(mob, "Backpack", None):
        state.pack_serial = mob.Backpack.Serial
        save_int("LumberjackPack", state.pack_serial)

    API.UseObject(state.pack_serial)
    API.Pause(1.0)

    state.runebook_serial = setup_target("LumberjackRunebook", "Target runebook")
    if not state.runebook_serial:
        stop_script("Runebook setup failed")
        return False

    state.drop_chest_serial = setup_drop_chest(first_run)
    if not state.drop_chest_serial:
        stop_script("Drop chest setup failed")
        return False

    state.rune_serial = setup_target("LumberjackRune", "Target recall rune")
    if not state.rune_serial:
        stop_script("Rune setup failed")
        return False

    return True


def wait_for_travel_to_lumber_spot(state, first_run):
    if not first_run:
        if not API.FindItem(state.drop_chest_serial):
            return True

    home_pos = (API.Player.X, API.Player.Y)

    while not API.StopRequested:
        dist = chebyshev_distance(API.Player.X, API.Player.Y, home_pos[0], home_pos[1])
        if dist > 50:
            return True
        API.Pause(1.0)
    return False


def get_equipped_axe(state):
    two_handed = API.FindLayer("TwoHanded")
    if two_handed and two_handed.Serial == state.axe_serial:
        return two_handed

    one_handed = API.FindLayer("OneHanded")
    if one_handed and one_handed.Serial == state.axe_serial:
        return one_handed

    return None


def ensure_axe_equipped(state):
    equipped = get_equipped_axe(state)
    if equipped:
        return equipped

    axe = API.FindItem(state.axe_serial)
    if not axe:
        return None

    dismount_if_mounted(delay=1.0)

    API.ClearLeftHand()
    API.Pause(1.0)
    API.ClearRightHand()
    API.Pause(1.0)

    API.EquipItem(axe.Serial)
    API.Pause(1.0)

    return get_equipped_axe(state)


def is_valid_tree(static):
    if getattr(static, "IsDestroyed", False):
        return False

    if getattr(static, "IsTree", False):
        return True

    if getattr(static, "Graphic", 0) in tree_graphics:
        return True

    if getattr(static, "IsVegetation", False) and getattr(
        static, "IsImpassible", False
    ):
        return True

    return False


def find_nearest_tree(state):
    px, py = API.Player.X, API.Player.Y
    statics = API.GetStaticsInArea(px - 16, py - 16, px + 16, py + 16)

    if not statics:
        return None

    now = time.time()
    player_z = API.Player.Z
    trees = {}

    for s in statics:
        if not is_valid_tree(s):
            continue

        if getattr(s, "Graphic", 0) in state.bad_graphics:
            continue

        key = (s.X, s.Y)

        if state.depleted_until.get(key, 0) > now:
            continue

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

    return min(trees.values(), key=lambda t: chebyshev_distance(px, py, t.X, t.Y))


def mark_depleted(state, tree):
    key = (tree.X, tree.Y)
    state.depleted_until[key] = time.time() + 180.0
    state.tree_attempts.pop(key, None)


def cleanup_depleted(state):
    now = time.time()
    state.depleted_until = {k: v for k, v in state.depleted_until.items() if v > now}
    state.tree_attempts = {
        k: v for k, v in state.tree_attempts.items() if k in state.depleted_until
    }


def chop_tree(state, tree):
    axe = ensure_axe_equipped(state)
    if not axe:
        stop_script("Could not equip axe")
        return False

    if API.HasTarget("any"):
        API.CancelTarget()
        API.Pause(0.1)
        API.Target(tree.X, tree.Y, tree.Z, tree.Graphic)
        wait_for_any(success_msgs + depleted_msgs + wait_msgs, 1.0)
        return True

    API.ClearJournal()

    dismount_if_mounted()

    API.UseObject(axe.Serial)
    if API.WaitForTarget(timeout=0.5) or API.HasTarget("any"):
        API.Target(tree.X, tree.Y, tree.Z, tree.Graphic)

    wait_for_any(success_msgs + depleted_msgs + wait_msgs, 1.0)
    return True


def chop_all_logs(state, recovery):
    no_progress = 0
    no_progress_limit = 12

    while not API.StopRequested:
        logs = API.FindTypeAll(0x1BDD, API.Backpack) or []
        if not logs:
            return True

        progressed_this_pass = False

        for log in logs:
            if API.StopRequested:
                return False

            before_amount = getattr(API.FindItem(log.Serial), "Amount", None)

            API.ClearJournal()
            if API.HasTarget("any"):
                API.CancelTarget()
                API.Pause(0.1)

            axe = ensure_axe_equipped(state)
            if not axe:
                stop_script("Could not equip axe")
                return False

            dismount_if_mounted()

            if not use_item_on_target(axe.Serial, log.Serial, timeout=0.5, delay=0.1):
                if API.WaitForTarget(timeout=1.5):
                    API.Target(log.Serial)
                    API.Pause(0.1)

            API.Pause(0.5)

            if API.InJournalAny(wait_msgs):
                API.Pause(0.5)

            after_item = API.FindItem(log.Serial)
            after_amount = getattr(after_item, "Amount", None) if after_item else None

            made_progress = (after_item is None) or (
                before_amount is not None and after_amount != before_amount
            )
            progressed_this_pass = progressed_this_pass or made_progress

        if progressed_this_pass:
            no_progress = 0
        else:
            no_progress += 1

        if no_progress >= no_progress_limit:
            if recovery.shutdown_cleanly():
                return False
            stop_script("Could not recover from stuck board conversion")
            return False

        # Dump boards after each batch
        if not dump_boards_to_pack(state):
            # Pack might be full, check if we should deposit
            boards_in_pack = count_items(0x1BD7, state.pack_serial)
            if boards_in_pack >= 1600:
                return True  # caller handles deposit routine

    return False


def dump_boards_to_pack(state):
    dest = state.pack_serial
    if not dest:
        return False

    if not is_pack_in_range(state):
        return False

    boards_in_backpack = count_items(0x1BD7, API.Backpack)
    if boards_in_backpack <= 0:
        return True

    existing = count_items(0x1BD7, dest)
    remaining = max(0, 1600 - existing)

    if remaining <= 0:
        return False

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


def harvest_tree(state, tree, recovery):
    px, py = API.Player.X, API.Player.Y
    dist = chebyshev_distance(px, py, tree.X, tree.Y)

    if dist > 1:
        if not API.Pathfind(tree.X, tree.Y, tree.Z, distance=1, wait=True, timeout=10):
            mark_depleted(state, tree)
            return

    key = (tree.X, tree.Y)
    API.ClearJournal()

    while not API.StopRequested:
        if is_heavy(buffer=60):
            if not chop_all_logs(state, recovery):
                return

            boards_in_pack = count_items(0x1BD7, state.pack_serial)
            if boards_in_pack >= 1600:
                return

            if is_heavy(buffer=60):
                break

        before_logs = count_items(0x1BDD, API.Backpack)
        before_boards = count_items(0x1BD7, API.Backpack)

        chop_tree(state, tree)
        API.Pause(0.1)

        after_logs = count_items(0x1BDD, API.Backpack)
        after_boards = count_items(0x1BD7, API.Backpack)

        progress = (after_logs > before_logs) or (after_boards > before_boards)

        if progress or API.InJournalAny(success_msgs):
            state.tree_attempts[key] = 0
        else:
            state.tree_attempts[key] = state.tree_attempts.get(key, 0) + 1

        if API.InJournalAny(depleted_msgs):
            if API.InJournalAny(["$[Cc]an.t use an axe", "cannot use an axe on that"]):
                graphic = getattr(tree, "Graphic", None)
                if graphic is not None:
                    graphic = int(graphic)
                    if graphic in tree_graphics:
                        tree_graphics.remove(graphic)
                    state.bad_graphics.add(graphic)
                    save_bad_graphics(state)
            mark_depleted(state, tree)
            break

        if API.InJournalAny(wait_msgs):
            API.Pause(0.5)

        if state.tree_attempts.get(key, 0) >= 6:
            mark_depleted(state, tree)
            break


def cast_mark(rune_serial):
    API.ClearJournal()
    API.CastSpell("Mark")

    if not API.WaitForTarget(timeout=5):
        return False

    API.Target(rune_serial)
    API.Pause(3.5)

    if API.InJournalAny(TRAVEL_FAIL_MSGS):
        return False

    return True


def deposit_routine(state):
    API.Dress("Main")
    API.Pause(1.5)

    rune = API.FindItem(state.rune_serial)
    if not rune:
        stop_script("Cannot find marking rune - check your backpack")
        return False

    if not cast_mark(state.rune_serial):
        stop_script("Failed to mark rune")
        return False

    if not recall_with_retry(
        state.runebook_serial,
        max_retries=MAX_TRAVEL_RETRIES,
        retry_delay=TRAVEL_RETRY_DELAY,
        use_sacred_journey=USE_SACRED_JOURNEY,
    ):
        stop_script(f"Failed to recall home after {MAX_TRAVEL_RETRIES} attempts")
        return False

    all_items = [0x1BD7] + bonus_lumberjack_items
    drop_all_items_at_home(
        state.drop_chest_serial, all_items, [API.Backpack, state.pack_serial]
    )

    if not recall_with_retry(
        state.rune_serial,
        max_retries=MAX_TRAVEL_RETRIES,
        retry_delay=TRAVEL_RETRY_DELAY,
        use_sacred_journey=USE_SACRED_JOURNEY,
    ):
        stop_script(
            f"Failed to recall back to lumber spot after {MAX_TRAVEL_RETRIES} attempts"
        )
        return False

    API.UseObject(state.pack_serial)
    API.Pause(1.0)

    return True


def main():
    if API.HasTarget("beneficial"):
        API.Stop()
        return
    if API.HasTarget("any"):
        API.CancelTarget()

    state = LumberjackState()
    state.bad_graphics = load_bad_graphics()

    first_run = load_int("LumberjackDropChest", 0) == 0
    if not setup_all_items(state, first_run):
        return

    recovery = Recovery(state.runebook_serial, 25)

    chest = API.FindItem(state.drop_chest_serial)
    boards = count_items(0x1BD7, API.Backpack) + count_items(0x1BD7, state.pack_serial)

    if chest and boards > 0:
        if not deposit_routine(state):
            stop_script("Failed to deposit on startup")
            return

    if not wait_for_travel_to_lumber_spot(state, first_run):
        return

    API.UseObject(state.pack_serial)
    API.Pause(1.0)

    while not API.StopRequested:
        if recovery.is_stuck():
            if recovery.shutdown_cleanly():
                return
            stop_script("Stuck and could not recall home")
            return

        axe = ensure_axe_equipped(state)
        if not axe:
            stop_script("Could not equip axe")
            break

        boards_in_pack = count_items(0x1BD7, state.pack_serial)
        if boards_in_pack >= 1600:
            if not deposit_routine(state):
                state.consecutive_failures += 1
                if state.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    if recovery.shutdown_cleanly():
                        return
                    stop_script("Recovery failed - stopping")
                    return
                break
            state.consecutive_failures = 0
            continue

        if is_heavy(buffer=60):
            if not chop_all_logs(state):
                break

            boards_in_pack = count_items(0x1BD7, state.pack_serial)
            if boards_in_pack >= 1600:
                if not deposit_routine(state):
                    state.consecutive_failures += 1
                    if state.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                        if recovery.shutdown_cleanly():
                            return
                        stop_script("Recovery failed - stopping")
                        return
                    break
                state.consecutive_failures = 0
                continue

            if is_heavy(buffer=60):
                if not is_pack_in_range(state):
                    if not wait_for_pack(state, timeout=30):
                        API.Pause(1.0)
                        continue

                dump_boards_to_pack(state)

                if is_heavy(buffer=60):
                    API.Pause(0.5)
                    continue

        cleanup_depleted(state)

        tree = find_nearest_tree(state)
        if not tree:
            state.no_trees_count += 1
            if state.no_trees_count >= 20:
                API.Dress("Main")
                API.Pause(1.5)
                recall_with_retry(
                    state.runebook_serial,
                    max_retries=5,
                    retry_delay=TRAVEL_RETRY_DELAY,
                    use_sacred_journey=USE_SACRED_JOURNEY,
                )
                break
            API.Pause(1.0)
            continue

        harvest_tree(state, tree, recovery)
        state.no_trees_count = 0
        state.consecutive_failures = 0

        boards_in_pack = count_items(0x1BD7, state.pack_serial)
        if boards_in_pack >= 1600:
            if not deposit_routine(state):
                state.consecutive_failures += 1
                if state.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    if recovery.shutdown_cleanly():
                        return
                    stop_script("Recovery failed - stopping")
                    return
                break
            state.consecutive_failures = 0

        API.Pause(0.1)


main()
