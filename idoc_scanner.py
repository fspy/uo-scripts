"""IDOC (In Danger of Collapsing) house scanner.

Scans for decaying house signs and tracks them in a JSON file.
"""

import enum
import json
import re
import subprocess
import threading
from datetime import datetime
from typing import List, Optional

import API

IDOC_FILE = "idoc_houses.json"
IDOC_RE = re.compile(r"condition: this structure is (.+).", re.I)
HOUSE_SIGN_NAME = "a house sign"
INTERESTING_CONDITIONS = {"greatly worn", "in danger of collapsing"}

_monitor_stop_event = threading.Event()
_is_monitoring = False


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
    if not IDOC_FILE:
        return {}
    try:
        with open(IDOC_FILE, "r") as f:
            data = json.load(f)
            for house in data.values():
                house["missed_count"] = 0
            return data
    except (ValueError, IOError):
        return {}


def save_houses(houses: dict) -> None:
    with open(IDOC_FILE, "w") as f:
        json.dump(houses, f, indent=2)


def idoc_monitor(monitor_chest: int, targets: List[int]) -> None:
    global _is_monitoring
    _is_monitoring = True
    _monitor_stop_event.clear()
    data = API.ItemNameAndProps(monitor_chest, True, 3)
    API.SysMsg(f"Monitoring! {data}")

    while data and not _monitor_stop_event.is_set():
        data = API.ItemNameAndProps(monitor_chest, True, 3)

        if any([x in data.lower() for x in ["locked down & secure", "a house sign"]]):
            API.Pause(0.05)
            continue

        while len(targets) > 0:
            t = targets.pop()
            API.QueueMoveItem(t, API.Backpack)

        subprocess.call(["curl", "-d", '"House Dropped!"', "ntfy.sh/idoc_fspy"])
        subprocess.call(
            [
                "ffplay",
                "-nodisp",
                "-autoexit",
                "/usr/share/sounds/ocean/stereo/phone-incoming-call.oga",
            ]
        )

    _is_monitoring = False
    API.SysMsg("Monitor stopped")


def idoc_setup() -> None:
    global _is_monitoring
    API.HeadMsg("target what to monitor (sign/chest)", API.Player)
    monitor = API.RequestTarget(60)

    API.HeadMsg("target chests to loot, esc when done", API.Player)
    targets = []
    req_tar = API.RequestTarget(60)
    while req_tar:
        targets.append(req_tar)
        API.Pause(0.5)
        req_tar = API.RequestTarget(60)

    _is_monitoring = True
    thread = threading.Thread(target=idoc_monitor, args=(monitor, targets), daemon=True)
    thread.start()


class IDOCScanner:
    GUMP_W = 290
    GUMP_H = 365
    GUMP_X = 40
    GUMP_Y = 40
    REFRESH_INTERVAL = 5
    POSITION_CHANGE_THRESHOLD = 3
    SCAN_RANGE = 24

    def __init__(self):
        self.houses: dict = {}
        self.gump = None
        self.scroll = None
        self.title_label = None
        self.monitor_button = None
        self.header_labels: dict = {}
        self.house_labels: dict = {}
        self.last_player_x: Optional[int] = None
        self.last_player_y: Optional[int] = None
        self.last_refresh_time: float = 0.0

    def on_gump_close(self) -> None:
        API.Stop()

    def on_monitor_click(self) -> None:
        global _is_monitoring
        if _is_monitoring:
            _is_monitoring = False
            _monitor_stop_event.set()
            self.rebuild_gump()
        else:
            idoc_setup()
            self.rebuild_gump()

    def make_pathfind_callback(self, house):
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

    def create_gump(self) -> None:
        self.gump = API.CreateModernGump(
            self.GUMP_X, self.GUMP_Y, self.GUMP_W, self.GUMP_H, True
        )

        self.scroll = API.Gumps.CreateGumpScrollArea(
            10, 30, self.GUMP_W - 20, self.GUMP_H - 70
        )
        self.gump.Add(self.scroll)

        self.title_label = API.CreateGumpTTFLabel(
            "", 20, "#ffffff", "IBMPlexSans-Medium"
        )
        self.title_label.SetRect(10, 5, self.GUMP_W - 20, 20)
        self.gump.Add(self.title_label)

        self.monitor_button = API.CreateSimpleButton(
            "Stop Monitor" if _is_monitoring else "Start Monitor", self.GUMP_W - 20, 25
        )
        self.monitor_button.SetRect(10, self.GUMP_H - 30, self.GUMP_W - 20, 25)
        self.gump.Add(self.monitor_button)
        API.Gumps.AddControlOnClick(self.monitor_button, self.on_monitor_click)

        self.header_labels = {}
        self.house_labels = {}

        API.Gumps.AddGump(self.gump)
        API.Gumps.AddControlOnDisposed(self.gump, self.on_gump_close)

    def rebuild_gump(self) -> None:
        if self.gump is None:
            self.create_gump()
        else:
            self.gump.Clear()  # type: ignore[union-attr]

        self.scroll = API.Gumps.CreateGumpScrollArea(
            10, 30, self.GUMP_W - 20, self.GUMP_H - 70
        )
        self.gump.Add(self.scroll)  # pyright: ignore reportOptionalMemberAccess

        self.title_label = API.CreateGumpTTFLabel(
            "", 20, "#ffffff", "IBMPlexSans-Medium"
        )
        self.title_label.SetRect(10, 5, self.GUMP_W - 20, 20)
        self.gump.Add(self.title_label)  # pyright: ignore reportOptionalMemberAccess

        self.monitor_button = API.CreateSimpleButton(
            "Stop Monitor" if _is_monitoring else "Start Monitor", self.GUMP_W - 20, 25
        )
        self.monitor_button.SetRect(10, self.GUMP_H - 30, self.GUMP_W - 20, 25)
        self.gump.Add(self.monitor_button)  # pyright: ignore reportOptionalMemberAccess
        API.Gumps.AddControlOnClick(self.monitor_button, self.on_monitor_click)

        self.header_labels = {}
        self.house_labels = {}

        by_facet = load_and_group_houses(self.houses)
        player_map = int(API.GetMap())

        total = sum(len(h) for h in by_facet.values())
        self.title_label.SetText(f"IDOC Scanner - {total} houses")

        y = 0
        for facet in sorted(
            by_facet.keys(), key=lambda f: Facet[f].value, reverse=True
        ):
            houses_list = by_facet[facet]

            header = API.CreateGumpTTFLabel(
                f"{facet.title()} ({len(houses_list)})",
                18,
                "#aaaaaa",
                "IBMPlexSans-Medium",
            )
            header.SetRect(5, y, self.GUMP_W - 30, 20)
            self.scroll.Add(header)
            self.header_labels[facet] = header
            y += 22

            for house in houses_list:
                dist = house["distance"] if house["map"] == player_map else None
                cond = house["condition"]
                cond_abbr = "IDOC" if "danger" in cond else " GW "
                color_hex = "#ff4444" if "danger" in cond else "#ffdd44"

                dist_str = f"{dist:>4}" if dist else " -- "
                text = f"{dist_str}  [{cond_abbr}]  {house['x']:4}, {house['y']:4}  {format_time(house['last_seen_at'])}"

                label = API.CreateGumpTTFLabel(
                    text, 18, color_hex, "IBMPlexMono-Medium"
                )
                label.SetRect(5, y, self.GUMP_W - 30, 18)
                self.scroll.Add(label)
                self.house_labels[house["serial"]] = label
                API.Gumps.AddControlOnClick(label, self.make_pathfind_callback(house))
                y += 20

            y += 8

        API.Gumps.AddGump(self.gump)

    def update_gump(self) -> None:
        by_facet = load_and_group_houses(self.houses)
        player_map = int(API.GetMap())

        total = sum(len(h) for h in by_facet.values())
        self.title_label.SetText(f"IDOC Scanner - {total} houses")  # pyright: ignore reportOptionalMemberAccess

        for facet in by_facet:
            houses_list = by_facet[facet]
            if facet in self.header_labels:
                self.header_labels[facet].SetText(
                    f"{facet.title()} ({len(houses_list)})"
                )

            for house in houses_list:
                serial = house["serial"]
                if serial in self.house_labels:
                    dist = house["distance"] if house["map"] == player_map else None
                    cond = house["condition"]
                    cond_abbr = "IDOC" if "danger" in cond else " GW "

                    dist_str = f"{dist:>4}" if dist else " -- "
                    text = f"{dist_str}  [{cond_abbr}]  {house['x']:4}, {house['y']:4}  {format_time(house['last_seen_at'])}"
                    self.house_labels[serial].SetText(text)

    def should_refresh(self) -> bool:
        current_x = API.Player.X
        current_y = API.Player.Y
        current_time = datetime.now().timestamp()

        if self.last_player_x is None or self.last_player_y is None:
            self.last_player_x = current_x
            self.last_player_y = current_y
            self.last_refresh_time = current_time
            return True

        moved = (
            abs(current_x - self.last_player_x) > self.POSITION_CHANGE_THRESHOLD
            or abs(current_y - self.last_player_y) > self.POSITION_CHANGE_THRESHOLD
        )

        time_elapsed = current_time - self.last_refresh_time > self.REFRESH_INTERVAL

        if moved:
            self.last_player_x = current_x
            self.last_player_y = current_y

        if time_elapsed or moved:
            self.last_refresh_time = current_time
            return True

        return False

    def main(self) -> None:
        self.houses = load_houses()
        self.rebuild_gump()

        while not API.StopRequested:
            API.ProcessCallbacks()

            if self.should_refresh():
                self.update_gump()

            player_x = API.Player.X
            player_y = API.Player.Y
            player_map = int(API.GetMap())

            removed = []
            for serial, house in self.houses.items():
                if house["map"] != player_map:
                    continue

                hx = house["x"]
                hy = house["y"]
                dist = int(((hx - player_x) ** 2 + (hy - player_y) ** 2) ** 0.5)

                if dist <= self.SCAN_RANGE:
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
                    house = self.houses[serial]
                    API.HeadMsg(f"Removed: {house['x']},{house['y']}", API.Player, 1000)
                    del self.houses[serial]
                save_houses(self.houses)
                self.rebuild_gump()

            ground = API.GetItemsOnGround(self.SCAN_RANGE)
            if not ground:
                API.Pause(1)
                continue

            house_signs = [
                s for s in ground if s.Name.lower() == HOUSE_SIGN_NAME.lower()
            ]
            refreshed_serials = []

            for sign in house_signs:
                data = API.ItemNameAndProps(sign, True)
                match = IDOC_RE.search(data)

                if not match:
                    continue

                condition = match.group(1).lower()
                serial_str = str(sign.Serial)

                if condition not in INTERESTING_CONDITIONS:
                    if serial_str in self.houses:
                        refreshed_serials.append(serial_str)
                    else:
                        API.HeadMsg(f"Found House\n{condition}", sign, 1000)
                        API.IgnoreObject(sign.Serial)
                    continue

                now = datetime.now().isoformat()
                x = int(sign.X)
                y = int(sign.Y)
                m = int(API.GetMap())

                if serial_str not in self.houses:
                    self.houses[serial_str] = {
                        "condition": condition,
                        "x": x,
                        "y": y,
                        "map": m,
                        "sign_serial": serial_str,
                        "first_seen_at": now,
                        "last_seen_at": now,
                        "missed_count": 0,
                    }
                    save_houses(self.houses)
                    self.rebuild_gump()
                    API.HeadMsg(
                        f"{condition.title()}: 0x{sign.Serial:X} ({get_facet_name(m)})",
                        sign,
                        253,
                    )
                else:
                    house = self.houses[serial_str]
                    house["last_seen_at"] = now
                    house["condition"] = condition
                    house["missed_count"] = 0
                    save_houses(self.houses)

            if refreshed_serials:
                for serial_str in refreshed_serials:
                    house = self.houses[serial_str]
                    API.HeadMsg(
                        f"Refreshed: {house['x']},{house['y']}", API.Player, 253
                    )
                    del self.houses[serial_str]
                save_houses(self.houses)
                self.rebuild_gump()

            API.Pause(1)


def main():
    scanner = IDOCScanner()
    scanner.main()


main()
