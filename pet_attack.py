from typing import List, cast

import API
from _lib.utils import p

blacklist = ["a rising colossus"]

target = API.NearestMobile(
    cast(
        List[API.Notoriety],
        [
            API.Notoriety.Criminal,
            API.Notoriety.Enemy,
            API.Notoriety.Gray,
            API.Notoriety.Murderer,
        ],
    ),
    10,
)

if target and target.HasLineOfSightFrom() and target.Name not in blacklist:
    if target.HitsDiff == 0:
        API.Virtue("Honor")
        if API.WaitForTarget(timeout=0.5):
            API.Target(target)  # pyright:ignore

    if API.Player.Mount:
        API.Dismount(True)
        while API.Player.Mount:
            API.Pause(0.05)

    pet = API.NearestMobile(cast(List[API.Notoriety], [API.Notoriety.Ally]))
    if pet:
        API.ContextMenu(pet.Serial, 1)
        if API.WaitForTarget(timeout=0.5):
            API.Target(target)  # pyright:ignore
            p(f"Attacking {target.Name}")
            API.HeadMsg("I'm so dead!", target)
