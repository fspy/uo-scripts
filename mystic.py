"""Mysticism Healing Bot"""

import time

import API
from _lib.utils import NOTORIETY_ENEMY, NOTORIETY_FRIENDLY

HEALTH_THRESHOLD = 0.8


def hits_pct(mobile):
    if mobile.HitsMax == 0:
        return 1
    return round(mobile.Hits / mobile.HitsMax, 1)


def get_target(range=10):
    damaged = sorted(
        filter(
            lambda x: hits_pct(x) <= HEALTH_THRESHOLD and x.HasLineOfSightFrom(),
            list(API.NearestMobiles(NOTORIETY_FRIENDLY, range)) + [API.Player],
        ),
        key=hits_pct,
    )

    if len(damaged) > 0:
        return damaged[0]

    return None


def get_spell(t):
    return (
        None
        if not t
        else "Cleansing Winds"
        if t.IsPoisoned or t.IsYellowHits
        else "Greater Heal"
    )


def main():
    follow_serial = 0x00006528
    last_peace = time.time()

    while not API.Player.IsDead:
        follow = API.FindMobile(follow_serial)
        if follow and follow.Distance < 6:
            API.AutoFollow(follow)

        enemies = API.NearestMobiles(NOTORIETY_ENEMY, 10)
        if len(enemies) > 0 and time.time() - last_peace > 10:
            API.UseSkill("Peacemaking")
            API.WaitForTarget()
            if len(enemies) == 1:
                API.Target(enemies[0])  # pyright:ignore
            else:
                API.TargetSelf()
            last_peace = time.time()

        t = get_target()
        s = get_spell(t)

        if not (t and s):
            API.Pause(0.1)
            continue

        API.CastSpell(s)
        if API.WaitForTarget("beneficial"):
            API.Target(t)  # pyright:ignore

        API.Pause(0.1)


main()
