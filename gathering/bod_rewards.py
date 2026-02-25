"""BOD Reward Claiming - monitors nearby profession NPCs and shows claimable rewards."""

import re

import API
from _lib.persistence import load_int, save_int
from _lib.utils import Hue, p

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
    "shadow_hammer": {
        "prof": "Blacksmith",
        "btn": 217,
        "desc": "Shadow Runic Hammer",
        "cost": 550,
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

PROF_TITLES = {
    "Tailor": "Tailor",
    "Weaver": "Tailor",
    "Blacksmith": "Blacksmith",
    "Armorer": "Blacksmith",
    "Weaponsmith": "Blacksmith",
}

BOD_GUMP = 0x69DA8520
CONFIRM_GUMP = 0x1440128A
NPC_RANGE = 3
POLL_INTERVAL = 0.3
GUMP_TIMEOUT = 1.5
POINTS_KEY_PREFIX = "BODPoints_"

GUMP_X = 100
GUMP_Y = 100
GUMP_WIDTH = 280
ROW_HEIGHT = 30
SECTION_HEADER_HEIGHT = 25
BUTTON_HEIGHT = 25
GUMP_PADDING = 15

current_npcs = {}  # {profession: {"serial": int, "points": int}}
gump_instance = None


def find_nearby_profession_npcs():
    """Find all profession NPCs within range. Returns {profession: serial}."""
    result = {}
    best_distance = {}
    npcs = API.NearestMobiles([API.Notoriety.Invulnerable], NPC_RANGE)  # pyright:ignore

    if not npcs:
        return result

    for npc in npcs:
        npc_name = API.ItemNameAndProps(npc, True)
        if not npc_name:
            continue
        npc_name = npc_name.split("\n")[0]

        match = re.match(r".+\s[Tt]he\s(\w+)$", npc_name)
        if not match:
            continue

        title = match.group(1)
        if title not in PROF_TITLES:
            continue

        profession = PROF_TITLES[title]
        distance = npc.Distance

        if profession not in result or distance < best_distance[profession]:
            result[profession] = npc.Serial
            best_distance[profession] = distance

    return result


def load_cached_points(profession):
    return load_int(
        f"{POINTS_KEY_PREFIX}{profession}", default=0, scope=API.PersistentVar.Char
    )


def save_cached_points(profession, points):
    save_int(
        f"{POINTS_KEY_PREFIX}{profession}", max(0, points), scope=API.PersistentVar.Char
    )


def query_points(npc_serial):
    """Query BOD points from NPC via context menu."""
    API.ContextMenu(npc_serial, 3)
    API.Pause(0.2)

    if not API.WaitForGump(BOD_GUMP, delay=GUMP_TIMEOUT):
        return 0

    contents = API.GetGumpContents(BOD_GUMP)
    API.ReplyGump(0, BOD_GUMP)

    if not contents or not contents.strip():
        return 0

    words = contents.split()
    if not words:
        return 0

    try:
        return int(words[-1].replace(",", ""))
    except ValueError:
        return 0


def read_points_from_gump():
    """Read points from currently open BOD reward gump."""
    if not API.HasGump(BOD_GUMP):
        return None

    contents = API.GetGumpContents(BOD_GUMP)
    if not contents or not contents.strip():
        return None

    words = contents.split()
    if not words:
        return None

    try:
        return int(words[-1].replace(",", ""))
    except ValueError:
        return None


def get_rewards_for_profession(profession):
    """Get rewards for profession, sorted by cost."""
    filtered = [
        (key, reward) for key, reward in REWARDS.items() if reward["prof"] == profession
    ]
    return sorted(filtered, key=lambda x: x[1]["cost"])


def make_refresh_callback(profession):
    def callback():
        refresh_points(profession)

    return callback


def refresh_points(profession):
    """Refresh points from NPC and update gump."""
    global current_npcs, gump_instance

    if profession not in current_npcs:
        return

    data = current_npcs[profession]
    serial = data["serial"]

    p(f"Refreshing {profession} points...", Hue.Cyan)

    new_points = query_points(serial)
    if new_points > 0:
        data["points"] = new_points
        save_cached_points(profession, new_points)
        p(f"{profession}: {new_points:,} points", Hue.Green)

        hide_gump()
        create_reward_gump()
    else:
        p(f"Failed to refresh {profession} points", Hue.Red)


def make_reward_callback(reward_key, profession):
    def callback():
        claim_reward(reward_key, profession)

    return callback


def create_reward_gump():
    """Create the reward gump showing all nearby professions."""
    global gump_instance

    if not current_npcs:
        return None

    total_rows = 0
    for profession in current_npcs:
        total_rows += 1
        total_rows += len(get_rewards_for_profession(profession))

    content_height = total_rows * ROW_HEIGHT
    gump_height = GUMP_PADDING * 2 + content_height

    g = API.CreateGump(True, True)
    g.SetX(GUMP_X)
    g.SetY(GUMP_Y)
    g.SetWidth(GUMP_WIDTH)
    g.SetHeight(gump_height)

    bg = API.CreateGumpColorBox(opacity=0.85, color="#1a1a2e")
    bg.SetX(0)
    bg.SetY(0)
    bg.SetWidth(GUMP_WIDTH)
    bg.SetHeight(gump_height)
    g.Add(bg)

    y_offset = GUMP_PADDING

    for profession in sorted(current_npcs.keys()):
        data = current_npcs[profession]
        points = data["points"]

        header_text = f"{profession} ({points:,} pts)"
        header = API.CreateGumpTTFLabel(header_text, 12, "#ffffff", "Arial Bold")
        header.SetX(10)
        header.SetY(y_offset)
        g.Add(header)

        refresh_btn = API.CreateSimpleButton("R", 20, 20)
        refresh_btn.SetX(GUMP_WIDTH - 35)
        refresh_btn.SetY(y_offset)
        g.Add(refresh_btn)
        API.AddControlOnClick(refresh_btn, make_refresh_callback(profession))

        y_offset += SECTION_HEADER_HEIGHT

        for key, reward in get_rewards_for_profession(profession):
            cost = reward["cost"]
            can_afford = points >= cost

            cost_text = f"[{cost}]"
            cost_color = "#00ff88" if can_afford else "#ff6666"

            cost_label = API.CreateGumpTTFLabel(cost_text, 11, cost_color, "Arial")
            cost_label.SetX(15)
            cost_label.SetY(y_offset + 5)
            g.Add(cost_label)

            btn = API.CreateSimpleButton(reward["desc"], GUMP_WIDTH - 80, BUTTON_HEIGHT)
            btn.SetX(60)
            btn.SetY(y_offset)
            g.Add(btn)

            API.AddControlOnClick(btn, make_reward_callback(key, profession))

            y_offset += ROW_HEIGHT

    API.AddGump(g)
    gump_instance = g
    return g


def claim_reward(reward_key, profession):
    """Claim a reward from the specified profession's NPC."""
    global current_npcs

    if profession not in current_npcs:
        p("NPC no longer nearby!", Hue.Red)
        return

    data = current_npcs[profession]
    reward = REWARDS.get(reward_key)

    if not reward:
        return

    if data["points"] < reward["cost"]:
        p(f"Not enough points! Need {reward['cost']}, have {data['points']}", Hue.Red)
        return

    p(f"Claiming {reward['desc']}...", Hue.Cyan)

    API.ContextMenu(data["serial"], 3)
    API.Pause(0.2)

    if not API.WaitForGump(BOD_GUMP, delay=GUMP_TIMEOUT):
        p("Failed to open reward gump!", Hue.Red)
        return

    fresh_points = read_points_from_gump()
    if fresh_points is not None:
        data["points"] = fresh_points
        save_cached_points(profession, fresh_points)

    API.ReplyGump(reward["btn"], BOD_GUMP)

    if API.WaitForGump(CONFIRM_GUMP, delay=GUMP_TIMEOUT):
        API.ReplyGump(2, CONFIRM_GUMP, [1])
        p(f"Claimed {reward['desc']}!", Hue.Green)

        data["points"] -= reward["cost"]
        save_cached_points(profession, data["points"])

        hide_gump()
        create_reward_gump()
    else:
        p("No confirmation gump appeared", Hue.Orange)


def hide_gump():
    global gump_instance
    if gump_instance:
        gump_instance.Dispose()
        gump_instance = None


def clear_state():
    global current_npcs, gump_instance
    hide_gump()
    current_npcs = {}


def main():
    global current_npcs, gump_instance

    p("BOD Reward Monitor started. Walk near a profession NPC.", Hue.Cyan)

    while not API.StopRequested:
        API.ProcessCallbacks()

        nearby = find_nearby_profession_npcs()

        old_profs = set(current_npcs.keys())
        new_profs = set(nearby.keys())
        added = new_profs - old_profs
        removed = old_profs - new_profs

        for prof in removed:
            del current_npcs[prof]

        for prof in added:
            serial = nearby[prof]
            cached = load_cached_points(prof)
            if cached > 0:
                points = cached
            else:
                points = query_points(serial)
                if points > 0:
                    save_cached_points(prof, points)

            current_npcs[prof] = {"serial": serial, "points": points}

        state_changed = added or removed

        if not current_npcs:
            if gump_instance is not None:
                hide_gump()
        elif state_changed:
            hide_gump()
            create_reward_gump()
        elif gump_instance is None and current_npcs:
            create_reward_gump()

        API.Pause(POLL_INTERVAL)

    clear_state()
    p("BOD Reward Monitor stopped.", Hue.Cyan)


main()
