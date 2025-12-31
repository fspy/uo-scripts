import API

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
ALL_DEPLETED_PAUSE = 15.0


def is_heavy() -> bool:
    if not API.Player or API.Player.WeightMax is None or API.Player.Weight is None:
        return False
    return API.Player.Weight >= (API.Player.WeightMax - WEIGHT_BUFFER)


def find_shovel():
    return API.FindType(SHOVEL_TYPE, API.Backpack)


def find_any_ore(min_amount: int = 0):
    for ore_type in ORE_TYPES:
        ore = API.FindType(ore_type, API.Backpack, minamount=min_amount)
        if ore:
            return ore
    return None


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

        # PreTarget must be set BEFORE the server requests a target.
        # If pretarget works correctly, a target cursor may never appear.
        API.PreTarget(beetle_serial)
        API.UseObject(ore.Serial)

        # If we DO get a target cursor, pretarget didn't apply; cancel it so we don't hang.
        if API.WaitForTarget(timeout=0.25):
            API.CancelTarget()

        API.Pause(SMELT_DELAY)
        API.CancelPreTarget()

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


PERSIST_KEY_BEETLE = "Mining.FireBeetleSerial"


def load_beetle_serial():
    # Persistent vars are stored as strings. Accept either decimal ("123") or hex ("0x123").
    serial_str = API.GetPersistentVar(PERSIST_KEY_BEETLE, "0", API.PersistentVar.Char)
    try:
        serial = int(str(serial_str).strip(), 0)
    except Exception:
        return 0

    if serial <= 0:
        return 0

    # Don't hard-fail if the mobile isn't currently in client awareness.
    # We'll still try to use the serial; you can retarget if needed.
    return serial


def save_beetle_serial(serial: int) -> None:
    API.SavePersistentVar(PERSIST_KEY_BEETLE, str(int(serial)), API.PersistentVar.Char)


beetle = load_beetle_serial()

if not beetle:
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
        # don't get stuck in an infinite "Heavy" loop.
        if is_heavy() and not find_smeltable_ore():
            API.SysMsg("Still heavy but no smeltable ore left; stopping")
            break

        API.Pause(0.25)
        continue

    # If all 4 tiles are depleted, wait and try again.
    if len(depleted_offsets) >= len(MINE_OFFSETS):
        depleted_offsets.clear()
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
