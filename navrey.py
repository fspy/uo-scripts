"""
Navrey Pillars Auto-Clicker

This script will attempt to use a nearby pillar in Navrey's arena.
The order of the pillars is randomized per boss spawn!
"""

from AutoComplete import *

while True:
    stone = Items.FindByID(0x03bf, 0, -1, 2)
    if stone:
        Items.UseItem(stone)
        Items.Message(stone, 1266, '* Clicked! *')
        Misc.Pause(625)
    Misc.Pause(50)