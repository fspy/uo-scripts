"""Scrap utilities and one-off scripts for TazUO Legion.

This file serves as a collection of miscellaneous utilities and quick scripts.
Most functions have been moved to appropriate _lib/ modules for reuse.

Usage:
    Run individual functions directly, or import from other scripts.
"""

# pyright: reportCallIssue=false

import API
from _lib.utils import h, p


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
            API.Pause(15)


# Uncomment to run specific functions:
# rb = 0x403C2DB3
# show_runebook_runes(rb)
# auto_coown()
