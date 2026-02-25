"""Scrap utilities and one-off scripts for TazUO Legion.

This file serves as a collection of miscellaneous utilities and quick scripts.
Most functions have been moved to appropriate _lib/ modules for reuse.

Usage:
    Run individual functions directly, or import from other scripts.
"""

# pyright: reportCallIssue=false

import API
from _lib.utils import Hue, h, p


def serpents_nest():
    """
    Lure nearby snakes to a Serpent's Nest.

    Detects serpent nests and snakes nearby, then uses snake charming
    flute to lure snakes to the nest.
    """
    while not API.StopRequested:
        nest_nearby = API.GetItemsOnGround(10, 0x2233) or []
        if len(nest_nearby) > 0:
            h("nest nearby!", API.Player, 1153)
        nearby_snakes = API.GetAllMobiles(0x005C, 10) + API.GetAllMobiles(0x0015, 10)

        if len(nest_nearby) == 0 or len(nearby_snakes) == 0:
            API.Pause(1)
            continue

        API.UseType(0x2805, 391, API.Backpack, True)
        API.WaitForTarget(timeout=1)
        API.Target(nearby_snakes[0])
        API.WaitForTarget(timeout=1)
        API.Target(nest_nearby[0])

        API.Pause(0.3)
        if API.InJournal("animal walks where it was instructed", True):
            API.IgnoreObject(nearby_snakes[0])
            API.Pause(8)


# Uncomment to run specific functions:
# rb = 0x403C2DB3
# show_runebook_runes(rb)
# auto_coown()

# thing = API.RequestAnyTarget()
# thing.Destroy()


def idoc_scanner():
    import json
    import os
    import re
    from datetime import datetime

    IDOC_FILE = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "idoc_houses.json"
    )
    idoc_re = re.compile(r"condition: this structure is (.+).", re.I)

    def load_known_houses():
        if not os.path.exists(IDOC_FILE):
            return set(), []
        try:
            with open(IDOC_FILE, "r") as f:
                houses = json.load(f)
            serials = {h["serial"] for h in houses}
            return serials, houses
        except (ValueError, IOError):
            return set(), []

    def save_houses(houses):
        with open(IDOC_FILE, "w") as f:
            json.dump(houses, f, indent=2)

    known_serials, houses_list = load_known_houses()

    while not API.StopRequested:
        ground = API.GetItemsOnGround(24)
        if not ground:
            continue

        house_signs = [s for s in ground if s.Name.lower() == "a house sign"]

        for sign in house_signs:
            data = API.ItemNameAndProps(sign, True)
            match = idoc_re.search(data)
            if not match:
                continue

            condition = match.group(1).lower()
            if condition not in ("greatly worn", "in danger of collapsing"):
                continue

            now = datetime.now().isoformat()
            serial = int(sign.Serial)
            x = int(sign.X)
            y = int(sign.Y)
            m = int(API.GetMap())

            if serial not in known_serials:
                houses_list.append(
                    {
                        "serial": serial,
                        "condition": condition,
                        "x": x,
                        "y": y,
                        "map": m,
                        "first_seen_at": now,
                        "last_seen_at": now,
                    }
                )
                known_serials.add(serial)
                save_houses(houses_list)
            else:
                for house in houses_list:
                    if house["serial"] == serial:
                        house["last_seen_at"] = now
                        house["condition"] = condition
                        save_houses(houses_list)
                        break

            API.IgnoreObject(serial)
            h(f"{condition.title()}: 0x{sign.Serial:X}", sign, Hue.Yellow)

        API.Pause(1)


def destroy_corpses():
    c = API.NearestCorpse()
    while c:
        c.Destroy()
        c = API.NearestCorpse()


# destroy_corpses()
if API.HasGump(0xB9D680BB):
    data = API.GetGumpContents(0xB9D680BB)
    p(data)
idoc_scanner()
