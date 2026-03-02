"""IDOC (In Danger of Collapsing) house scanner.

Scans for decaying house signs and tracks them in a JSON file.
"""

import enum
import json
import re
from datetime import datetime
from typing import Optional

import API

IDOC_FILE = "idoc_houses.json"
IDOC_RE = re.compile(r"condition: this structure is (.+).", re.I)
SCAN_RANGE = 24
HOUSE_SIGN_NAME = "a house sign"
INTERESTING_CONDITIONS = {"greatly worn", "in danger of collapsing"}


def format_time(iso_str):
    try:
        house_time = datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%S.%f")
        diff = datetime.now() - house_time
        seconds = diff.total_seconds()

        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m"
        elif seconds < 86400:
            return f"{int(seconds / 3600)}h"
        else:
            return f"{int(seconds / 86400)}d"

    except Exception as e:
        API.SysMsg(str(e))
        return f"?({e})"


class Facet(enum.Enum):
    Felucca = 0
    Trammel = 1
    Ilshenar = 2
    Malas = 3
    Tokuno = 4
    TerMur = 5


def get_facet_name(map_idx: int) -> str:
    """Convert map index to facet name."""
    try:
        return Facet(map_idx).name
    except ValueError:
        return f"Unknown({map_idx})"


def get_distance(x, y):
    px, py = API.Player.X, API.Player.Y
    return int(((x - px) ** 2 + (y - py) ** 2) ** 0.5)


def load_and_group_houses(houses):
    by_facet = {}
    for serial, house in houses.items():
        house["serial"] = serial
        dist = get_distance(house["x"], house["y"])
        house["distance"] = dist
        facet = Facet(house["map"]).name
        by_facet.setdefault(facet, []).append(house)

    for facet in by_facet:
        by_facet[facet].sort(
            key=lambda h: (h["x"], h["y"], h["condition"] != "in danger of collapsing")
        )

    return by_facet


def load_houses() -> dict:
    """Load known houses from JSON file. Returns dict keyed by serial."""
    if not IDOC_FILE:
        return {}
    try:
        with open(IDOC_FILE, "r") as f:
            data = json.load(f)
            for house in data.values():
                house["missed_count"] = 0  # runtime only, not saved
            return data
    except (ValueError, IOError):
        return {}


def save_houses(houses: dict) -> None:
    """Save houses dict to JSON file."""
    with open(IDOC_FILE, "w") as f:
        json.dump(houses, f, indent=2)


GUMP_W = 290
GUMP_H = 365
GUMP_X = 40
GUMP_Y = 40

current_gump_id = None
last_player_x = None
last_player_y = None
last_refresh_time = 0
REFRESH_INTERVAL = 5  # seconds
POSITION_CHANGE_THRESHOLD = 3
houses = {}

gump: Optional[API.ApiUiBaseControl] = None
scroll = None
title_label = None
header_labels = {}
house_labels = {}


def on_gump_close():
    """Called when gump is closed by user."""
    API.Stop()


def make_pathfind_callback(house):
    def callback():
        player_map = int(API.GetMap())
        if house["map"] != player_map:
            API.HeadMsg("Different facet", API.Player, 1000)
            return

        dist = house.get("distance", 999)
        if dist <= 100:
            API.Pathfind(house["x"], house["y"], 0)
        else:
            API.HeadMsg("Too far", API.Player, 1000)

    return callback


def create_gump():
    """Create gump and all controls once."""
    global gump, scroll, title_label, header_labels, house_labels

    gump = API.Gumps.CreateModernGump(GUMP_X, GUMP_Y, GUMP_W, GUMP_H, True)

    # bg = API.Gumps.CreateGumpColorBox(opacity=0.8, color="#1A1A1A")
    # bg.SetRect(0, 0, GUMP_W, GUMP_H)
    # gump.Add(bg)

    scroll = API.Gumps.CreateGumpScrollArea(10, 30, GUMP_W - 20, GUMP_H - 40)
    gump.Add(scroll)

    title_label = API.CreateGumpTTFLabel("", 20, "#ffffff", "IBMPlexSans-Medium")
    title_label.SetRect(10, 5, GUMP_W - 20, 20)
    gump.Add(title_label)

    header_labels = {}
    house_labels = {}

    API.Gumps.AddGump(gump)
    API.Gumps.AddControlOnDisposed(gump, on_gump_close)


def rebuild_gump():
    """Recreate gump content from scratch (for structural changes)."""
    global gump, scroll, title_label, header_labels, house_labels, current_gump_id

    if not gump:
        create_gump()
    else:
        gump.Clear()

    current_gump_id = gump

    scroll = API.Gumps.CreateGumpScrollArea(10, 30, GUMP_W - 20, GUMP_H - 40)
    gump.Add(scroll)

    title_label = API.CreateGumpTTFLabel("", 20, "#ffffff", "IBMPlexSans-Medium")
    title_label.SetRect(10, 5, GUMP_W - 20, 20)
    gump.Add(title_label)

    header_labels = {}
    house_labels = {}

    by_facet = load_and_group_houses(houses)
    player_map = int(API.GetMap())

    total = sum(len(h) for h in by_facet.values())
    title_label.SetText(f"IDOC Scanner - {total} houses")

    y = 0
    for facet in sorted(by_facet.keys(), key=lambda f: Facet[f].value, reverse=True):
        houses_list = by_facet[facet]

        header = API.CreateGumpTTFLabel(
            f"{facet.title()} ({len(houses_list)})",
            18,
            "#aaaaaa",
            "IBMPlexSans-Medium",
        )
        header.SetRect(5, y, GUMP_W - 30, 20)
        scroll.Add(header)
        header_labels[facet] = header
        y += 22

        for house in houses_list:
            dist = house["distance"] if house["map"] == player_map else None
            cond = house["condition"]
            cond_abbr = "IDOC" if "danger" in cond else " GW "
            color_hex = "#ff4444" if "danger" in cond else "#ffdd44"

            dist_str = f"{dist:>4}" if dist else " -- "
            text = f"{dist_str}  [{cond_abbr}]  {house['x']:4}, {house['y']:4}  {format_time(house['last_seen_at'])}"

            label = API.CreateGumpTTFLabel(text, 18, color_hex, "IBMPlexMono-Medium")
            label.SetRect(5, y, GUMP_W - 30, 18)
            scroll.Add(label)
            house_labels[house["serial"]] = label
            API.Gumps.AddControlOnClick(label, make_pathfind_callback(house))
            y += 20

        y += 8


def update_gump():
    """Update labels in-place (no rebuild)."""
    global title_label, header_labels, house_labels

    by_facet = load_and_group_houses(houses)
    player_map = int(API.GetMap())

    total = sum(len(h) for h in by_facet.values())
    title_label.SetText(f"IDOC Scanner - {total} houses")

    for facet in by_facet:
        houses_list = by_facet[facet]
        if facet in header_labels:
            header_labels[facet].SetText(f"{facet.title()} ({len(houses_list)})")

        for house in houses_list:
            serial = house["serial"]
            if serial in house_labels:
                dist = house["distance"] if house["map"] == player_map else None
                cond = house["condition"]
                cond_abbr = "IDOC" if "danger" in cond else " GW "

                dist_str = f"{dist:>4}" if dist else " -- "
                text = f"{dist_str}  [{cond_abbr}]  {house['x']:4}, {house['y']:4}  {format_time(house['last_seen_at'])}"
                house_labels[serial].SetText(text)


def should_refresh():
    global last_player_x, last_player_y, last_refresh_time

    current_x = API.Player.X
    current_y = API.Player.Y
    current_time = datetime.now().timestamp()

    # Initialize on first call
    if last_player_x is None or last_player_y is None:
        last_player_x = current_x
        last_player_y = current_y
        last_refresh_time = current_time
        return True

    # Check if player moved
    moved = (
        abs(current_x - last_player_x) > POSITION_CHANGE_THRESHOLD
        or abs(current_y - last_player_y) > POSITION_CHANGE_THRESHOLD
    )

    # Check if time-based refresh needed
    time_elapsed = current_time - last_refresh_time > REFRESH_INTERVAL

    if moved:
        last_player_x = current_x
        last_player_y = current_y

    if time_elapsed or moved:
        last_refresh_time = current_time
        return True

    return False


def main():
    global houses
    houses = load_houses()
    rebuild_gump()

    while not API.StopRequested:
        API.ProcessCallbacks()

        if should_refresh():
            update_gump()

        # Check for fallen houses BEFORE ground scan
        player_x = API.Player.X
        player_y = API.Player.Y
        player_map = int(API.GetMap())

        removed = []
        for serial, house in houses.items():
            if house["map"] != player_map:
                continue

            hx = house["x"]
            hy = house["y"]
            dist = int(((hx - player_x) ** 2 + (hy - player_y) ** 2) ** 0.5)

            if dist <= SCAN_RANGE:
                item = API.FindItem(int(serial))
                if item:
                    house["missed_count"] = 0
                    API.HeadMsg(
                        f"{house['condition'].title()}: 0x{int(serial):X}",
                        item,
                        253,
                    )
                else:
                    house["missed_count"] = house.get("missed_count", 0) + 1
                    if house["missed_count"] >= 3:
                        removed.append(serial)

        if removed:
            for serial in removed:
                house = houses[serial]
                API.HeadMsg(f"Removed: {house['x']},{house['y']}", API.Player, 1000)
                del houses[serial]
            save_houses(houses)
            rebuild_gump()

        ground = API.GetItemsOnGround(SCAN_RANGE)
        if not ground:
            API.Pause(1)
            continue

        house_signs = [s for s in ground if s.Name.lower() == HOUSE_SIGN_NAME.lower()]
        refreshed_serials = []

        for sign in house_signs:
            data = API.ItemNameAndProps(sign, True)
            match = IDOC_RE.search(data)

            if not match:
                continue

            condition = match.group(1).lower()
            serial_str = str(sign.Serial)

            if condition not in INTERESTING_CONDITIONS:
                # If this was a tracked house, it has been refreshed
                if serial_str in houses:
                    refreshed_serials.append(serial_str)
                else:
                    API.HeadMsg(f"Found House\n{condition}", sign, 1000)
                    API.IgnoreObject(sign.Serial)
                continue

            now = datetime.now().isoformat()
            x = int(sign.X)
            y = int(sign.Y)
            m = int(API.GetMap())

            if serial_str not in houses:
                houses[serial_str] = {
                    "condition": condition,
                    "x": x,
                    "y": y,
                    "map": m,
                    "sign_serial": serial_str,
                    "first_seen_at": now,
                    "last_seen_at": now,
                    "missed_count": 0,
                }
                save_houses(houses)
                rebuild_gump()
                API.HeadMsg(
                    f"{condition.title()}: 0x{sign.Serial:X} ({get_facet_name(m)})",
                    sign,
                    253,
                )
            else:
                house = houses[serial_str]
                house["last_seen_at"] = now
                house["condition"] = condition
                house["missed_count"] = 0
                save_houses(houses)

        # Remove houses that have been refreshed (no longer GW/IDOC)
        if refreshed_serials:
            for serial_str in refreshed_serials:
                house = houses[serial_str]
                API.HeadMsg(f"Refreshed: {house['x']},{house['y']}", API.Player, 253)
                del houses[serial_str]
            save_houses(houses)
            rebuild_gump()

        API.Pause(1)


main()
