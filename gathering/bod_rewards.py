"""BOD Reward Claiming for TazUO Legion Scripts.

Monitors for nearby profession NPCs and displays a gump with claimable rewards.
Shows current points balance filtered by profession.

Features:
- Multi-profession support: shows rewards from all nearby NPCs
- Points caching: persists points per-character, updates on claim
- Simple range check: gump appears when within 3 tiles of NPC

Usage:
- Run script, it monitors in background
- Walk within 3 tiles of profession NPCs (Blacksmith, Tailor, etc.)
- Gump appears with rewards for all nearby professions
- Click a reward to claim it
- Walk away and gump hides
"""

import re

import API
from _lib.persistence import load_int, save_int
from _lib.utils import Hue, p

# Debug flag - set to True to see verbose logging
DEBUG = False


def dbg(msg):
    """Print debug message if DEBUG is enabled."""
    if DEBUG:
        p(f"[DBG] {msg}", Hue.Gray)


# =============================================================================
# REWARDS CONFIGURATION
# =============================================================================

REWARDS = {
    "horned_kit": {
        "prof": "Tailor",
        "btn": 222,
        "desc": "Horned Runic Sewing Kit",
        "cost": 600,
    },
    "pof": {
        "prof": "Blacksmith",
        "btn": 212,
        "desc": "Powder of Fortifying",
        "cost": 450,
    },
    "copper_hammer": {
        "prof": "Blacksmith",
        "btn": 223,
        "desc": "Copper Runic Hammer",
        "cost": 650,
    },
    "bronze_hammer": {
        "prof": "Blacksmith",
        "btn": 225,
        "desc": "Bronze Runic Hammer",
        "cost": 700,
    },
}

# NPC title -> normalized profession name
PROF_TITLES = {
    "Tailor": "Tailor",
    "Weaver": "Tailor",
    "Blacksmith": "Blacksmith",
    "Armorer": "Blacksmith",
    "Weaponsmith": "Blacksmith",
}

# =============================================================================
# CONSTANTS
# =============================================================================

BOD_GUMP = 0x69DA8520
CONFIRM_GUMP = 0x1440128A

# Single range for detection and action
NPC_RANGE = 3

POLL_INTERVAL = 0.3
GUMP_TIMEOUT = 1.5

# Persistence key prefix for cached points
POINTS_KEY_PREFIX = "BODPoints_"

# Gump layout
GUMP_X = 100
GUMP_Y = 100
GUMP_WIDTH = 280
ROW_HEIGHT = 30
SECTION_HEADER_HEIGHT = 25
BUTTON_HEIGHT = 25
GUMP_PADDING = 15

# =============================================================================
# STATE
# =============================================================================

# {profession: {"serial": int, "points": int}}
current_npcs = {}
gump_instance = None


# =============================================================================
# NPC DETECTION
# =============================================================================


def find_nearby_profession_npcs():
    """
    Find all profession NPCs within NPC_RANGE.

    Returns:
        dict: {profession: serial} for each unique profession in range.
              Only keeps the closest NPC per profession.
    """
    result = {}
    best_distance = {}
    npcs = API.NearestMobiles([API.Notoriety.Invulnerable], NPC_RANGE)  # pyright:ignore

    if not npcs:
        return result

    dbg(f"Found {len(npcs)} invulnerable mobiles within range {NPC_RANGE}")

    for npc in npcs:
        try:
            npc_name = API.ItemNameAndProps(npc, True).split("\n")[0]
        except Exception:
            continue

        # Match "Name The Title" pattern
        match = re.match(r".+\s[Tt]he\s(\w+)$", npc_name)
        if not match:
            continue

        title = match.group(1)
        if title not in PROF_TITLES:
            continue

        profession = PROF_TITLES[title]
        distance = npc.Distance

        dbg(f"  MATCH: {profession} serial=0x{npc.Serial:X} dist={distance}")

        # Keep only the closest NPC for each profession
        if profession not in result or distance < best_distance[profession]:
            result[profession] = npc.Serial
            best_distance[profession] = distance

    return result


# =============================================================================
# POINTS QUERY
# =============================================================================


def load_cached_points(profession):
    """Load cached points for a profession from persistence."""
    return load_int(
        f"{POINTS_KEY_PREFIX}{profession}", default=0, scope=API.PersistentVar.Char
    )


def save_cached_points(profession, points):
    """Save points for a profession to persistence."""
    save_int(
        f"{POINTS_KEY_PREFIX}{profession}", max(0, points), scope=API.PersistentVar.Char
    )


def query_points(npc_serial):
    """
    Query current BOD points from NPC via context menu.

    Opens reward gump, parses points from last word, closes gump.

    Args:
        npc_serial: Serial of the profession NPC

    Returns:
        int: Current points balance, or 0 if query failed
    """
    dbg(f"query_points: serial=0x{npc_serial:X}")
    API.ContextMenu(npc_serial, 3)  # "Claim Rewards" (0-indexed, fourth option)
    API.Pause(0.2)

    if not API.WaitForGump(BOD_GUMP, delay=GUMP_TIMEOUT):
        dbg("query_points: gump did not appear!")
        return 0

    try:
        contents = API.GetGumpContents(BOD_GUMP)
        dbg(f"query_points: contents='{contents[:80] if contents else 'None'}...'")
        API.ReplyGump(0, BOD_GUMP)  # Close gump properly

        if not contents or not contents.strip():
            return 0

        # Points is the last word, may have commas (e.g., "1,500")
        words = contents.split()
        if not words:
            return 0

        points_str = words[-1].replace(",", "")
        points = int(points_str)
        dbg(f"query_points: parsed points={points}")
        return points
    except Exception as e:
        p(f"Failed to parse points: {e}", Hue.Orange)
        API.ReplyGump(0, BOD_GUMP)
        return 0


def read_points_from_gump():
    """
    Read points from currently open BOD reward gump.

    Returns:
        int: Points value, or None if gump not open or parse failed
    """
    if not API.HasGump(BOD_GUMP):
        return None

    try:
        contents = API.GetGumpContents(BOD_GUMP)
        if not contents or not contents.strip():
            return None

        words = contents.split()
        if not words:
            return None

        points_str = words[-1].replace(",", "")
        return int(points_str)
    except Exception:
        return None


# =============================================================================
# GUMP CREATION
# =============================================================================


def get_rewards_for_profession(profession):
    """Get list of (key, reward) tuples filtered by profession, sorted by cost."""
    filtered = [
        (key, reward) for key, reward in REWARDS.items() if reward["prof"] == profession
    ]
    return sorted(filtered, key=lambda x: x[1]["cost"])


def make_reward_callback(reward_key, profession):
    """Create a callback function for a reward button."""

    def callback():
        claim_reward(reward_key, profession)

    return callback


def create_reward_gump():
    """
    Create the reward gump showing all nearby professions.

    Uses current_npcs state to determine what to show.
    Professions are sorted alphabetically.
    """
    global gump_instance

    if not current_npcs:
        dbg("create_reward_gump: no NPCs, skipping")
        return None

    dbg(f"create_reward_gump: professions={list(current_npcs.keys())}")

    # Calculate dynamic height based on all professions and their rewards
    total_rows = 0
    for profession in current_npcs:
        total_rows += 1  # Section header
        rewards = get_rewards_for_profession(profession)
        total_rows += len(rewards)

    content_height = total_rows * ROW_HEIGHT
    gump_height = GUMP_PADDING * 2 + content_height

    # Create gump
    g = API.CreateGump(True, True)  # movable, closeable
    g.SetX(GUMP_X)
    g.SetY(GUMP_Y)
    g.SetWidth(GUMP_WIDTH)
    g.SetHeight(gump_height)

    # Background
    bg = API.CreateGumpColorBox(opacity=0.85, color="#1a1a2e")
    bg.SetX(0)
    bg.SetY(0)
    bg.SetWidth(GUMP_WIDTH)
    bg.SetHeight(gump_height)
    g.Add(bg)

    y_offset = GUMP_PADDING

    # Sort professions alphabetically
    for profession in sorted(current_npcs.keys()):
        data = current_npcs[profession]
        points = data["points"]

        # Section header: "Blacksmith (1,500 pts)"
        header_text = f"{profession} ({points:,} pts)"
        header = API.CreateGumpTTFLabel(header_text, 12, "#ffffff", "Arial Bold")
        header.SetX(10)
        header.SetY(y_offset)
        g.Add(header)

        y_offset += SECTION_HEADER_HEIGHT

        # Reward buttons for this profession
        rewards = get_rewards_for_profession(profession)

        for key, reward in rewards:
            cost = reward["cost"]
            desc = reward["desc"]
            can_afford = points >= cost

            # Cost label
            cost_text = f"[{cost}]"
            cost_color = "#00ff88" if can_afford else "#ff6666"

            cost_label = API.CreateGumpTTFLabel(cost_text, 11, cost_color, "Arial")
            cost_label.SetX(15)
            cost_label.SetY(y_offset + 5)
            g.Add(cost_label)

            # Reward button
            btn = API.CreateSimpleButton(desc, GUMP_WIDTH - 80, BUTTON_HEIGHT)
            btn.SetX(60)
            btn.SetY(y_offset)
            g.Add(btn)

            # Attach callback
            API.AddControlOnClick(btn, make_reward_callback(key, profession))

            y_offset += ROW_HEIGHT

    # Show gump (no on_disposed callback - it was causing issues)
    API.AddGump(g)
    gump_instance = g
    dbg("create_reward_gump: gump added")

    return g


# =============================================================================
# REWARD CLAIMING
# =============================================================================


def claim_reward(reward_key, profession):
    """
    Claim a reward from the specified profession's NPC.

    Opens context menu, reads fresh points from gump, selects reward, confirms,
    then subtracts cost locally and updates cache.
    """
    global current_npcs

    if profession not in current_npcs:
        p("NPC no longer nearby!", Hue.Red)
        return

    data = current_npcs[profession]
    reward = REWARDS.get(reward_key)

    if not reward:
        p(f"Unknown reward: {reward_key}", Hue.Red)
        return

    # Check if we can afford it
    if data["points"] < reward["cost"]:
        p(f"Not enough points! Need {reward['cost']}, have {data['points']}", Hue.Red)
        return

    p(f"Claiming {reward['desc']}...", Hue.Cyan)

    # Open reward gump via context menu
    npc_serial = data["serial"]
    API.ContextMenu(npc_serial, 3)
    API.Pause(0.2)

    if not API.WaitForGump(BOD_GUMP, delay=GUMP_TIMEOUT):
        p("Failed to open reward gump!", Hue.Red)
        return

    # Read fresh points from gump and update cache
    fresh_points = read_points_from_gump()
    if fresh_points is not None:
        data["points"] = fresh_points
        save_cached_points(profession, fresh_points)

    # Select the reward
    API.ReplyGump(reward["btn"], BOD_GUMP)

    # Wait for confirmation gump
    if API.WaitForGump(CONFIRM_GUMP, delay=GUMP_TIMEOUT):
        API.ReplyGump(2, CONFIRM_GUMP, [1])  # Confirm with switch
        p(f"Claimed {reward['desc']}!", Hue.Green)

        # Subtract cost locally and update cache
        data["points"] -= reward["cost"]
        save_cached_points(profession, data["points"])

        # Recreate gump with updated points
        hide_gump()
        create_reward_gump()
    else:
        p("No confirmation gump appeared", Hue.Orange)


# =============================================================================
# GUMP MANAGEMENT
# =============================================================================


def hide_gump():
    """Hide the reward gump if visible."""
    global gump_instance
    if gump_instance:
        dbg("hide_gump: disposing gump")
        try:
            gump_instance.Dispose()
        except Exception as e:
            dbg(f"hide_gump: dispose failed: {e}")
        gump_instance = None


def clear_state():
    """Clear all tracking state."""
    global current_npcs, gump_instance
    hide_gump()
    current_npcs = {}


# =============================================================================
# MAIN LOOP
# =============================================================================


def main():
    """Main loop - monitors NPC proximity and manages gump."""
    global current_npcs, gump_instance

    p("BOD Reward Monitor started. Walk near a profession NPC.", Hue.Cyan)

    while not API.StopRequested:
        # Process button click callbacks
        API.ProcessCallbacks()

        # 1. Detect all profession NPCs in range
        nearby = find_nearby_profession_npcs()

        # 2. Determine what changed
        old_profs = set(current_npcs.keys())
        new_profs = set(nearby.keys())
        added = new_profs - old_profs
        removed = old_profs - new_profs

        # 3. Handle removed NPCs
        for prof in removed:
            dbg(f"NPC left range: {prof}")
            del current_npcs[prof]

        # 4. Handle added NPCs - query points for each
        for prof in added:
            serial = nearby[prof]
            dbg(f"NPC entered range: {prof} serial=0x{serial:X}")

            # Try cached points first
            cached = load_cached_points(prof)
            if cached > 0:
                dbg(f"  Using cached points: {cached}")
                points = cached
            else:
                # Query fresh points
                points = query_points(serial)
                if points > 0:
                    save_cached_points(prof, points)

            current_npcs[prof] = {"serial": serial, "points": points}

        # 5. Update gump if anything changed
        state_changed = added or removed

        if not current_npcs:
            # No NPCs nearby - hide gump if showing
            if gump_instance is not None:
                dbg("No NPCs nearby, hiding gump")
                hide_gump()
        elif state_changed:
            # NPCs changed - recreate gump
            dbg(f"State changed, recreating gump: {list(current_npcs.keys())}")
            hide_gump()
            create_reward_gump()
        elif gump_instance is None and current_npcs:
            # Gump missing but should exist - recreate
            # (Can happen if user closed it manually)
            dbg("Gump missing, recreating")
            create_reward_gump()

        API.Pause(POLL_INTERVAL)

    # Cleanup on stop
    clear_state()
    p("BOD Reward Monitor stopped.", Hue.Cyan)


main()
