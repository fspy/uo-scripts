import API
from _lib.utils import NOTORIETY_ENEMY, NOTORIETY_FRIENDLY, Hue, h

blacklist = ["a rising colossus"]

target = API.NearestMobile(NOTORIETY_ENEMY, 10)
pet = [mob for mob in API.NearestMobiles(NOTORIETY_FRIENDLY, 12) if mob.IsRenamable]
if len(pet) == 0:
    API.Stop()

pet = pet[0]
if target and target.HasLineOfSightFrom(API.Player) and target.Name not in blacklist:
    if target.HitsDiff == 0:
        API.Virtue("Honor")
        if API.WaitForTarget(timeout=0.5):
            API.Target(target)  # pyright:ignore

    if API.Player.Mount:
        API.Dismount(True)
        while API.Player.Mount:
            API.Pause(0.05)

    API.ContextMenu(pet.Serial, 1)
    if API.WaitForTarget(timeout=0.5):
        API.Target(target)  # pyright:ignore
        h("ATTACKING", target, Hue.Red)

else:
    API.ContextMenu(pet.Serial, 1)
