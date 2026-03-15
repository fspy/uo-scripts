import random
import threading
import time
from typing import cast

import API
from _lib.utils import NOTORIETY_ENEMY, NOTORIETY_FRIENDLY, Hue, h, play_audio


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
        API.Target(nearby_snakes[0])  # pyright:ignore
        API.WaitForTarget(timeout=1)
        API.Target(nest_nearby[0])  # pyright:ignore

        API.Pause(0.3)
        if API.InJournal("animal walks where it was instructed", True):
            API.IgnoreObject(nearby_snakes[0])
            API.Pause(8)


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
