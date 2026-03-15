import re
import time

import API

DRY_RUN = False
DESTROY_CLEARED = False
MAX_RANGE = 2

LOOT_NAMES_EXACT = set(
    [
        "abyssal cloth",
        "bark fragment",
        "blight",
        "blood of the dark father",
        "blue diamond",
        "boura pelt",
        "brilliant amber",
        "corrosive ash",
        "corruption",
        "crushed glass",
        "crystal shards",
        "crystalline blackrock",
        "daemon claw",
        "dark sapphire",
        "delicate scales",
        "ecru citrine",
        "faery dust",
        "fey wings",
        "fire ruby",
        "goblin blood",
        "lava serpent crust",
        "luminescent fungi",
        "muculent",
        "parasitic plant",
        "perfect emerald",
        "putrefaction",
        "raptor teeth",
        "reflective wolf eye",
        "scourge",
        "seed of renewal",
        "silver serpent venom",
        "silver snake skin",
        "slith tongue",
        "spider carapace",
        "switch",
        "taint",
        "turquoise",
        "undying flesh",
        "vial of vitriol",
        "void core",
        "void essence",
        "void orb",
        "white pearl",
        "resolve's bridle",
        "quartz grit",
        "daemon bone",
        "grapeshot",
        "powder charge",
        "fuse cord",
        "cannonball",
        "crystal of shame",
        "cursed oilstone",
        "a message in a bottle",
        "recipe scroll",
        "zoogi fungus",
        "ethereal sand",
    ]
)

LOOT_NAME_REGEX_RAW = [
    r"essence of .+",
    r"([4-9]\d{3,}) gold coin",
    r".+crystal of shame",
]

HUE_CLEARED = 73
HUE_MATCH = 62

STABLE_S = 0.20
POLL_S = 0.05
MAX_STABLE_WAIT_S = 1.5
EMPTY_CORPSE_GRACE_S = 0.75

RETRY_SOON_S = 0.10
RETRY_FAR_S = 0.50
DONE_TTL_S = 15 * 60

MAX_ENQUEUE_PER_TICK = 1

corpse_state = {}


LOOT_NAME_REGEX = [re.compile(p, re.IGNORECASE) for p in LOOT_NAME_REGEX_RAW if p]


def name_matches_loot(name):
    if not name:
        return False
    n = name.strip().lower()
    if n in LOOT_NAMES_EXACT:
        return True
    for pat in LOOT_NAME_REGEX:
        if pat.search(n):
            return True
    return False


def get_move_interval_s():
    if API.Profile and API.Profile.MoveItemDelay:
        return max(0.25, float(API.Profile.MoveItemDelay) / 1000.0)
    return 0.66


MOVE_INTERVAL_S = get_move_interval_s()

if not LOOT_NAMES_EXACT and not LOOT_NAME_REGEX:
    API.SysMsg("LOOT_NAMES_EXACT / LOOT_NAME_REGEX are empty", 33)
    API.Stop()

lootbag = (
    API.Profile.LootBagSerial
    if API.Profile and API.Profile.LootBagSerial
    else API.Backpack
)


def wait_stable_contents(serial):
    start = time.time()
    last = API.Contents(serial)
    last_change = time.time()
    while time.time() - start < MAX_STABLE_WAIT_S:
        cur = API.Contents(serial)
        if cur != last:
            last = cur
            last_change = time.time()
        elif time.time() - last_change >= STABLE_S:
            return True
        API.Pause(POLL_S)
    return False


def scan_ground_corpses():
    items = API.GetItemsOnGround(MAX_RANGE) or []
    corpses = [i for i in items if i.IsCorpse and i.Distance <= MAX_RANGE]
    corpses.sort(key=lambda c: c.Distance)
    return corpses


def scan_targets_from_corpse(corpse_serial):
    targets = {}
    for it in API.ItemsInContainer(corpse_serial, False):
        if name_matches_loot(it.Name):
            targets[it.Serial] = it.Name
    return targets


def item_still_in_corpse(item_serial, corpse_serial):
    it = API.FindItem(item_serial)
    return it and it.Container == corpse_serial


API.SysMsg(
    f"Autoloot V2 DRY_RUN={DRY_RUN} DESTROY_CLEARED={DESTROY_CLEARED} "
    f"LootBag=0x{int(lootbag):X} MoveInterval={MOVE_INTERVAL_S:.2f}s",
    946,
)

while True:
    corpses = scan_ground_corpses()
    if not corpses:
        API.Pause(0.10)
        continue

    t = time.time()

    for corpse in corpses:
        corpse_serial = corpse.Serial

        st = corpse_state.get(corpse_serial)
        if st is None:
            st = {
                "state": "NEW",
                "next_try_at": 0.0,
                "last_seen": t,
                "empty_streak": 0,
                "targets": {},
                "move_cooldown_until": 0.0,
                "opened_at": 0.0,
                "seen_nonzero_contents": False,
            }
            corpse_state[corpse_serial] = st

        st["last_seen"] = t

        if t < st["next_try_at"]:
            continue

        if corpse.Distance > MAX_RANGE:
            st["state"] = "FAR"
            st["next_try_at"] = time.time() + RETRY_FAR_S
            continue

        if st["state"] == "DONE" and t < st["next_try_at"]:
            continue

        if not corpse.Opened:
            API.UseObject(corpse_serial)
            st["state"] = "OPENING"
            st["opened_at"] = time.time()
            st["seen_nonzero_contents"] = False
            st["empty_streak"] = 0
            st["next_try_at"] = time.time() + RETRY_SOON_S
            continue

        if API.Contents(corpse_serial) > 0:
            st["seen_nonzero_contents"] = True

        if not wait_stable_contents(corpse_serial):
            st["state"] = "RETRY_STABLE"
            st["next_try_at"] = time.time() + RETRY_SOON_S
            continue

        current = scan_targets_from_corpse(corpse_serial)

        for item_serial in list(st["targets"].keys()):
            if item_serial not in current:
                del st["targets"][item_serial]

        for item_serial, nm in current.items():
            if item_serial not in st["targets"]:
                st["targets"][item_serial] = {"name": nm, "tries": 0, "last_try": 0.0}

        if not st["targets"]:
            can_declare_empty = st["seen_nonzero_contents"] or (
                st["opened_at"]
                and (time.time() - st["opened_at"]) >= EMPTY_CORPSE_GRACE_S
            )
            if not can_declare_empty:
                st["state"] = "WAIT_POPULATE"
                st["next_try_at"] = time.time() + RETRY_SOON_S
                continue

            st["empty_streak"] += 1
            if st["empty_streak"] >= 2:
                corpse.SetHue(HUE_CLEARED)
                if (not DRY_RUN) and DESTROY_CLEARED:
                    corpse.Destroy()
                st["state"] = "DONE"
                st["next_try_at"] = time.time() + DONE_TTL_S
                st["empty_streak"] = 0
            else:
                st["next_try_at"] = time.time() + 0.05
            continue

        st["empty_streak"] = 0

        if DRY_RUN:
            API.HeadMsg(f"MATCH ({len(st['targets'])})", corpse_serial, HUE_MATCH)
            st["state"] = "MATCH_DRY"
            st["next_try_at"] = time.time() + 0.50
            continue

        if API.IsProcessingMoveQueue() or API.IsGlobalCooldownActive():
            st["state"] = "WAIT_QUEUE"
            st["next_try_at"] = time.time() + 0.05
            continue

        if time.time() < st["move_cooldown_until"]:
            st["state"] = "WAIT_MOVE_COOLDOWN"
            st["next_try_at"] = time.time() + 0.05
            continue

        enq = 0
        for item_serial, meta in st["targets"].items():
            if enq >= MAX_ENQUEUE_PER_TICK:
                break
            if not item_still_in_corpse(item_serial, corpse_serial):
                continue
            if time.time() - meta["last_try"] < MOVE_INTERVAL_S:
                continue
            API.QueueMoveItem(item_serial, lootbag, 0)
            meta["tries"] += 1
            meta["last_try"] = time.time()
            st["move_cooldown_until"] = meta["last_try"] + MOVE_INTERVAL_S
            enq += 1

        st["state"] = "LOOTING"
        st["next_try_at"] = time.time() + (0.05 if enq else RETRY_SOON_S)

    API.Pause(0.02)
