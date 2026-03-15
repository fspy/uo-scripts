"""Scrap utilities and one-off scripts for TazUO Legion.

This file serves as a collection of miscellaneous utilities and quick scripts.
Most functions have been moved to appropriate _lib/ modules for reuse.

Usage:
    Run individual functions directly, or import from other scripts.
"""

# pyright: reportCallIssue=false

import json
import random
import re
import threading
import time
from collections import defaultdict
from typing import cast

import API
from _lib.utils import NOTORIETY_ENEMY, NOTORIETY_FRIENDLY, Hue, h, p, play_audio


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


def move_resource(res=100):
    what = API.FindItem(API.RequestTarget())
    where = API.RequestTarget()
    while API.HasGump(0x23D0F169):
        API.ReplyGump(res, 0x23D0F169)
        API.WaitForGump(0x23D0F169)
        i = API.FindType(what.Graphic, API.Backpack)
        if i and API.Player.Weight > 500:
            API.QueueMoveItem(i, where, i.Amount)
            while API.IsProcessingMoveQueue():
                API.Pause(0.01)
            API.Pause(0.01)

        API.Pause(0.01)


def dump_container():
    cont = API.FindItem(API.RequestTarget())
    if not cont:
        API.Stop()

    API.UseObject(cont)
    API.Pause(0.663)

    def container_data():
        try:
            with open("containers.json", "r") as f:
                data = json.load(f)
                return data
        except (ValueError, IOError):
            return defaultdict(list)

    data = container_data()
    data[str(cont.Serial)] = sorted([item.Name for item in API.ItemsInContainer(cont)])

    with open("containers.json", "w") as f:
        json.dump(data, f, indent=2)


def afk_farming():
    last_close_mobs = 0

    while not API.StopRequested:
        people = [
            m
            for m in API.NearestMobiles(
                NOTORIETY_FRIENDLY + [cast(API.Notoriety, API.Notoriety.Invulnerable)],
                24,
            )
            if not (m.IsRenamable or m.Serial == API.Player.Serial)
        ]
        close_mobs = [
            m
            for m in API.NearestMobiles(NOTORIETY_ENEMY, 8)
            if not m.HasLineOfSightFrom(API.Player)
        ]

        if not people and not close_mobs:
            API.Pause(0.1)
            return

        close_people = [m for m in people if m.Distance <= 12]
        low_hp = (
            (API.Player.Hits / API.Player.HitsMax) < 0.9
            if API.Player.HitsMax
            else False
        )

        if close_people:
            h(f"People are nearby!\n{', '.join(z.Name for z in people)}")
            thread = threading.Thread(
                target=play_audio,
                args=("/usr/share/sounds/ocean/stereo/phone-incoming-call.oga",),
                daemon=True,
            )
            thread.start()
            wiggle()

        if close_mobs and (time.time() - last_close_mobs) > 2:
            h(f"No Line of Sight!\n{', '.join(z.Name for z in close_mobs)}")
            thread = threading.Thread(
                target=play_audio,
                args=("/usr/share/sounds/ocean/stereo/bell.oga",),
                daemon=True,
            )
            thread.start()
            last_close_mobs = time.time()

        if low_hp:
            h("Low HP!", hue=Hue.Red)
            thread = threading.Thread(
                target=play_audio,
                args=("/usr/share/sounds/ocean/stereo/dialog-warning.oga",),
                daemon=True,
            )
            thread.start()

        API.Pause(0.1)


def wiggle():
    for _ in range(10):
        API.Walk(
            random.choice(
                (
                    "north",
                    "south",
                    "east",
                    "west",
                    "northeast",
                    "northwest",
                    "southeast",
                    "southwest",
                )
            )
        )
        API.Pause(0.1)


def honesty():
    items = API.GetItemsOnGround(24)
    if not items:
        return

    for i, item in enumerate(items):
        tooltip = API.ItemNameAndProps(item)

        if "Lost Item" in tooltip:
            API.HeadMsg("Lost Item!", API.Player)
            API.TrackingArrow(item.X, item.Y, i)

            while item.Distance > 2:
                API.Pathfind(item.X, item.Y, item.Z, 1, True)
                API.Pause(0.1)

            API.MoveItem(item, API.Backpack)
            API.TrackingArrow(-1, -1, i)

    API.Pause(0.1)


def skill_jewelry_finder(min=30):
    for item in API.ItemsInContainer(API.RequestTarget(), recursive=True):
        sum = 0
        for prop in item.NameAndProps(True).split("\n"):
            match = re.match(r"(?:.+) \+(\d+)$", prop)
            if match:
                sum += int(match.group(1))

        if sum > min:
            p(f"{item.Name} +{sum}")
            yield item

    p("Done!")


def color_paperdoll(hue=0x4000):
    LAYERS = [
        "OneHanded",
        "TwoHanded",
        "Shoes",
        "Pants",
        "Shirt",
        "Helmet",
        "Gloves",
        "Ring",
        "Talisman",
        "Necklace",
        "Hair",
        "Waist",
        "Torso",
        "Bracelet",
        "Face",
        "Beard",
        "Tunic",
        "Earrings",
        "Arms",
        "Cloak",
        "Backpack",
        "Robe",
        "Skirt",
        "Legs",
        "Mount",
    ]
    person = API.FindMobile(API.RequestAnyTarget())  # pyright:ignore
    if not person:
        API.Stop()

    for y in LAYERS:
        item = API.FindLayer(y, person)
        if item:
            item.SetHue(hue)


# for item in skill_jewelry_finder(min=30):
#     API.MoveItem(item, API.Backpack)
#     API.Pause(0.633)


def move_resource_box(source=None, destination=None):
    GUMP_ID = 0x23D0F169
    ITEM_RE = re.compile(r"^([A-Za-z]+)$", re.MULTILINE)
    QTY_RE = re.compile(r"^(\d+)$", re.MULTILINE)
    BUTTON_RE = re.compile(
        r"^button\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)$", re.MULTILINE
    )

    def parse_gump_packet_text(text):
        item_names = ITEM_RE.findall(text)
        quantities = QTY_RE.findall(text)
        button_ids = [int(b) for b in BUTTON_RE.findall(text) if int(b) >= 100]

        items = list(zip(item_names, [int(q) for q in quantities]))
        paired = list(zip(items, button_ids))

        return [btn for (_, qty), btn in paired if qty > 0]

    if not source:
        h("target source resource box")
        tar = API.RequestTarget(30)
        if not tar:
            return
        source = API.FindItem(tar)

    if not destination:
        h("target destination resource box")
        tar = API.RequestTarget(30)
        if not tar:
            return
        destination = API.FindItem(tar)

    # open destination gump
    API.UseObject(destination)
    API.WaitForGump(GUMP_ID)
    # click button
    API.ReplyGump(1, GUMP_ID)
    API.WaitForTarget()

    # open source gump
    API.UseObject(source)
    API.WaitForGump(GUMP_ID)
    # should still have cursor

    while API.HasGump(GUMP_ID):
        text = API.GetGump(GUMP_ID).PacketGumpText
        buttons = parse_gump_packet_text(text)

        if not buttons:
            return

        btn = buttons.pop()

        if API.Player.WeightMax - API.Player.Weight < 50:
            API.Target(API.Backpack)
            API.WaitForTarget()

        API.ReplyGump(btn, GUMP_ID)
        API.WaitForGump(GUMP_ID)

    # workaround since same gump id
    # click "add"
    # parse gumps
    # click buttons
    # target backpack

    # while API.HasGump():
    #     text = API.GetGump(0x23D0F169).PacketGumpText
    #     buttons = parse_gump_packet_text(text)


move_resource_box()
