"""
Automated BOD (Bulk Order Deed) Collector

Automatically collects BODs from all profession NPCs at Luna, stores them,
and tracks an 18-hour cooldown per character. Script enforces running only
once per day (when all 8 professions have 3 BODs available).

Usage:
- Run script from any location
- Must have a recall rune in backpack for return trip
- Must be at home (near HOME location) to use "Luna Mint" command for outbound travel
"""

import re
import time
from typing import cast

import API
from _lib.persistence import load_int, save_int
from _lib.utils import Hue, h, p

HOME = {"x": 1871, "y": 2494, "z": 7, "map": 0}
LUNA_EAST = {"x": 996, "y": 520, "z": -50, "map": 3}
LUNA_WEST = {"x": 984, "y": 520, "z": -50, "map": 3}

HOME_CONTAINER = 0x400561EC
STANDALONES = 0x4044F319
REGULAR = 0x4156F901

PROFESSIONS = {
    "Alchemy",
    "Blacksmith",
    "Carpentry",
    "Cooking",
    "Fletching",
    "Inscription",
    "Tailoring",
    "Tinkering",
}

SKILLS = {
    "Alchemy": ["Alchemist"],
    "Blacksmith": ["Blacksmith"],
    "Carpentry": ["Carpenter"],
    "Cooking": ["Cook"],
    "Fletching": ["Bowyer"],
    "Inscription": ["Scribe"],
    "Tailoring": ["Tailor", "Weaver"],
    "Tinkering": ["Tinker"],
}

BOD_GUMP_IDS = (0x9BADE6EA, 0xBE0DAD1E)
ACCEPT_BUTTON = 1
CONTEXT_MENU_BOD_INFO = 1
RUNE_GRAPHIC = 0x1F14

EIGHTEEN_HOURS = 18 * 60 * 60
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2.0

LAST_RUN_KEY = "BODLastRun"


def check_daily_run_guard():
    """Check if 18 hours have passed since last run. Exit if not ready."""
    last_run = load_int(
        LAST_RUN_KEY, default=0, scope=cast(API.PersistentVar, API.PersistentVar.Char)
    )

    if last_run == 0:
        return

    elapsed = time.time() - last_run
    if elapsed < EIGHTEEN_HOURS:
        remaining = EIGHTEEN_HOURS - elapsed
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        p(f"BODs not ready. {hours}h {minutes}m remaining.", Hue.Red)
        API.Stop()


def save_last_run():
    """Save current timestamp as last successful run."""
    save_int(
        LAST_RUN_KEY,
        int(time.time()),
        scope=cast(API.PersistentVar, API.PersistentVar.Char),
    )
    p("BOD collection complete. Next run available in 18 hours.", Hue.Green)


def is_at_location(loc, range=15):
    """Check if player is at/near a location."""
    return (
        loc["map"] == API.GetMap()
        and abs(API.Player.X - loc["x"]) <= range
        and abs(API.Player.Y - loc["y"]) <= range
    )


def detect_location():
    """Detect current location. Returns 'home', 'luna_east', 'luna_west', or 'unknown'."""
    if is_at_location(HOME):
        return "home"
    if is_at_location(LUNA_EAST):
        return "luna_east"
    if is_at_location(LUNA_WEST):
        return "luna_west"
    return "unknown"


def verify_travel(old_pos, min_distance=10, timeout=5.0):
    """Verify that position changed significantly after travel."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if (
            abs(API.Player.X - old_pos[0]) > min_distance
            or abs(API.Player.Y - old_pos[1]) > min_distance
        ):
            return True
        API.Pause(0.1)
    return False


def wait_for_arrival(loc, range=3, timeout=8.0):
    """Wait until player arrives at specific location coordinates."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if is_at_location(loc, range=range):
            return True
        if API.Pathfinding():
            API.Pause(0.2)
        else:
            if is_at_location(loc, range=range * 2):
                return True
            API.Pause(0.1)
    return is_at_location(loc, range=range * 2)


def travel_home_to_luna():
    """Travel from home to Luna using 'Luna Mint' command."""
    old_pos = (API.Player.X, API.Player.Y)

    for attempt in range(1, RETRY_ATTEMPTS + 1):
        p(f"Traveling to Luna (attempt {attempt}/{RETRY_ATTEMPTS})...")
        API.Msg("Luna Mint")
        API.Pause(1.0)

        if verify_travel(old_pos, min_distance=50):
            p("Arrived at Luna.", Hue.Green)
            return True

        if attempt < RETRY_ATTEMPTS:
            API.Pause(RETRY_DELAY)

    p("Failed to travel to Luna.", Hue.Red)
    return False


def travel_to_location(loc):
    """Walk to a specific location within Luna."""
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        p(f"Walking to location (attempt {attempt}/{RETRY_ATTEMPTS})...")
        API.Pause(0.7)
        API.Pathfind(loc["x"], loc["y"], loc["z"], distance=0, timeout=10)

        if wait_for_arrival(loc, range=0, timeout=8.0):
            return True

        if attempt < RETRY_ATTEMPTS:
            API.Pause(RETRY_DELAY)

    return False


def travel_east_to_west():
    """Walk from Luna East to Luna West."""
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        p(f"Walking to Luna West (attempt {attempt}/{RETRY_ATTEMPTS})...")
        API.Pathfind(
            LUNA_WEST["x"], LUNA_WEST["y"], LUNA_WEST["z"], distance=0, timeout=10
        )

        if wait_for_arrival(LUNA_WEST, range=0, timeout=8.0):
            p("Arrived at Luna West.", Hue.Green)
            return True

        if attempt < RETRY_ATTEMPTS:
            API.Pause(RETRY_DELAY)

    p("Failed to walk to Luna West.", Hue.Red)
    return False


def recall_home():
    """Recall home using rune from backpack."""
    rune = API.FindType(RUNE_GRAPHIC, API.Backpack)
    if not rune:
        p("No recall rune found in backpack!", Hue.Red)
        return False

    spell = "Sacred Journey" if API.GetSkill("Chivalry").Value > 60 else "Recall"
    old_pos = (API.Player.X, API.Player.Y)

    for attempt in range(1, RETRY_ATTEMPTS + 1):
        p(f"Recalling home (attempt {attempt}/{RETRY_ATTEMPTS})...")
        API.ClearJournal()
        API.CastSpell(spell)

        if not API.WaitForTarget(timeout=5):
            p("No target cursor - retrying...", Hue.Orange)
            if attempt < RETRY_ATTEMPTS:
                API.Pause(RETRY_DELAY)
            continue

        API.Target(rune.Serial)  # type: ignore
        API.Pause(0.5)

        if verify_travel(old_pos, min_distance=50):
            p("Arrived home.", Hue.Green)
            return True

        if API.InJournalAny(["fizzle", "blocked", "not powerful enough", "too heavy"]):
            p("Recall failed - retrying...", Hue.Orange)

        if attempt < RETRY_ATTEMPTS:
            API.Pause(RETRY_DELAY)

    p("Failed to recall home.", Hue.Red)
    return False


def get_trained_skills():
    """Get skills that character actually has trained (value > 0)."""
    return {
        skill: npcs for skill, npcs in SKILLS.items() if API.GetSkill(skill).Value > 0
    }


def find_profession_npcs(trained_skills):
    """Find nearby profession NPCs matching trained skills."""
    matches = {}
    npcs = API.NearestMobiles([API.Notoriety.Invulnerable], 10)  # type: ignore

    for npc in npcs:
        try:
            npc_name = API.ItemNameAndProps(npc, True).split("\n")[0]
        except Exception as _:
            continue

        match = re.match(r".+The\s([^\s]+)$", npc_name)
        if not match:
            continue

        profession_title = match.group(1)

        for skill_name, npc_titles in trained_skills.items():
            if profession_title in npc_titles:
                matches[skill_name] = npc.Serial
                break

    return matches


def accept_bod_gump():
    """Accept BOD if gump is open."""
    for gump_id in BOD_GUMP_IDS:
        if API.HasGump(gump_id):
            API.ReplyGump(ACCEPT_BUTTON, gump_id)
            API.Pause(0.1)
            return True
    return False


def request_bod_from_npc(npc_serial):
    """
    Request BOD from NPC. Returns:
    - True: Successfully collected BOD
    - False: NPC on cooldown (got "offer may be available" message)
    - None: Error or no response
    """
    API.ClearJournal()
    API.ContextMenu(npc_serial, CONTEXT_MENU_BOD_INFO)
    API.Pause(0.3)

    if API.InJournal("offer may be available in about", True):
        return False

    deadline = time.time() + 3.0
    while time.time() < deadline:
        if accept_bod_gump():
            return True
        API.Pause(0.1)

    return None


def collect_from_profession(profession, npc_serial, pending):
    """Collect all 3 BODs from a single profession NPC."""
    if profession not in pending:
        return False

    if accept_bod_gump():
        p(f"Accepted pending {profession} BOD", Hue.Green)

    bods_collected = 0
    max_attempts = 5

    for _ in range(max_attempts):
        result = request_bod_from_npc(npc_serial)

        if result is True:
            bods_collected += 1
            p(f"Collected {profession} BOD #{bods_collected}", Hue.Green)
            API.Pause(0.1)
        elif result is False:
            if bods_collected > 0:
                p(f"{profession} complete: {bods_collected} BODs collected", Hue.Green)
            else:
                p(f"{profession} on cooldown (no BODs available)", Hue.Orange)
            pending.remove(profession)
            return True
        else:
            p(
                f"Failed to get {profession} BOD after {bods_collected} collected",
                Hue.Red,
            )
            if bods_collected > 0:
                pending.remove(profession)
            return None

    if bods_collected > 0:
        p(
            f"{profession} complete: {bods_collected} BODs collected (hit max attempts)",
            Hue.Green,
        )
        pending.remove(profession)
    return True


def find_container():
    """Check if home container is nearby."""
    items = API.GetItemsOnGround(2)
    if not items:
        return False
    for item in items:
        if item.Serial == HOME_CONTAINER:
            return True
    return False


def drop_bods():
    """Drop all BODs from backpack into storage books."""
    if not find_container():
        p("Home container not found!", Hue.Red)
        return False

    if not API.FindType(0x2258, API.Backpack):
        p("No BODs to store.", Hue.Orange)
        return True

    p("Storing BODs...")
    API.UseObject(HOME_CONTAINER)
    API.Pause(0.3)
    API.ContextMenu(STANDALONES, 2)
    API.Pause(0.2)
    API.ContextMenu(REGULAR, 2)
    API.Pause(0.5)
    return True


def main():
    """Main BOD collection routine."""
    p("Starting BOD collection...", Hue.Cyan)

    check_daily_run_guard()

    trained_skills = get_trained_skills()
    if not trained_skills:
        p("No trained profession skills found!", Hue.Red)
        return

    pending = set(trained_skills.keys())
    p(f"Collecting BODs for: {', '.join(sorted(pending))}")

    location = detect_location()
    p(f"Current location: {location}")

    if location == "home":
        if not travel_home_to_luna():
            p("Failed to reach Luna. Aborting.", Hue.Red)
            return
        p("Walking to Luna East bank...")
        if not travel_to_location(LUNA_EAST):
            p("Failed to reach Luna East. Aborting.", Hue.Red)
            return
        location = "luna_east"
    elif location == "unknown":
        p("Attempting to reach Luna East...")
        if travel_to_location(LUNA_EAST):
            location = "luna_east"
        else:
            p("Unknown location. Please start at home or Luna.", Hue.Red)
            return

    while pending and not API.StopRequested:
        remaining_skills = {k: v for k, v in trained_skills.items() if k in pending}
        npcs = find_profession_npcs(remaining_skills)

        if npcs:
            p(f"Found NPCs for: {', '.join(npcs.keys())}")

            for profession, npc_serial in npcs.items():
                if profession not in pending:
                    continue
                collect_from_profession(profession, npc_serial, pending)
                API.Pause(0.05)
        else:
            p("No profession NPCs found nearby.", Hue.Orange)

        if not pending:
            p("All professions collected!", Hue.Green)
            break

        if location == "luna_east":
            if not travel_east_to_west():
                p(
                    "Failed to reach Luna West. Continuing with what we have...",
                    Hue.Orange,
                )
                break
            location = "luna_west"
        elif location == "luna_west":
            p("Finished scanning Luna.", Hue.Cyan)
            break

    if pending:
        p(f"Could not collect from: {', '.join(sorted(pending))}", Hue.Orange)

    if recall_home():
        p("Walking to home storage location...")
        if travel_to_location(HOME):
            drop_bods()
            if not pending:
                save_last_run()
            h("All done!", hue=Hue.Cyan)
        else:
            p("Failed to reach storage location. BODs remain in backpack.", Hue.Red)
    else:
        p("Failed to return home. BODs remain in backpack.", Hue.Red)


main()
