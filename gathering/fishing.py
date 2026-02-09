import os

import API
from _lib.utils import p

fishIds = [
    0x09CC,
    0x09CD,
    0x09CE,
    0x09CF,
    0x4302,
    0x4303,
    0x4306,
    0x4307,
    0x44C3,
    0x44C4,
    0x44C5,
    0x44C6,
]
shoeIds = [0x170F, 0x170D, 0x1711, 0x170C, 0x170E, 0x1712, 0x170B, 0x1710]
fishSteakIds = [0x097B, 0x097A]

bigFishIds = [17158, 17159, 17156, 17157]

relative_locations = [
    (i, j) for i in range(-3, 4) for j in range(-3, 4) if (i, j) != (0, 0)
]
pole = API.FindLayer("OneHanded") or API.FindType(0x0DC0, API.Backpack)

if not pole:
    API.Stop()


def _cutAndDropFish():
    weightDiff = API.Player.WeightMax - API.Player.Weight
    if weightDiff > 35:
        return
    for fishId in fishIds:
        fishes = API.FindTypeAll(fishId, API.Backpack)
        for fish in fishes:
            API.UseType(0x0F52, 0, API.Backpack)
            API.WaitForTarget()
            API.Target(fish.Serial)  # pyright:ignore
            API.Pause(0.25)
    for bigFishId in bigFishIds:
        bigFishes = API.FindTypeAll(bigFishId, API.Backpack)
        for bigFish in bigFishes:
            API.MoveItemOffset(bigFish.Serial, -1, 1, OSI=True)


def rel(x, y):
    return x - API.Player.X, y - API.Player.Y


def fish(x, y):
    API.UseObject(pole)
    API.WaitForTarget()
    rx, ry = rel(x, y)
    tile = API.GetTile(rx, ry)
    API.Target(rx, ry, tile.Z)


def mass_fish():
    for x, y in relative_locations:
        while not API.InJournal("fish don't seem to", True):
            _cutAndDropFish()
            fish(x, y)
            API.Pause(0.3)

            if API.InJournal("already fishing", True):
                API.Pause(0.65)
                continue

            if API.InJournalAny(
                [
                    "fish don't seem to",
                    "cannot be seen",
                    "need to be closer",
                ],
                True,
            ):
                break

            while not API.InJournalAny(["You pull out", "You fish a while"], True):
                API.Pause(0.1)


def single_fish():
    t = API.RequestAnyTarget()
    x, y = rel(t.X, t.Y)
    while True:
        API.UseObject(pole)
        API.WaitForTarget()
        # API.TargetLandRel(x, y)
        API.Target(t.X, t.Y, t.Z, t.Graphic)
        API.Pause(1)

        if API.InJournal("don't seem to be biting"):
            break


# mass_fish()
single_fish()
os.system("mpv /usr/share/sounds/ocean/stereo/battery-low.oga")
