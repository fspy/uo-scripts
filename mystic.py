import API
from _lib.utils import p

HEALTH_THRESHOLD = 0.8


def hits_pct(mobile):
    if mobile.HitsMax == 0:
        return 1
    return round(mobile.Hits / mobile.HitsMax, 1)


def get_target(range=10):
    damaged = sorted(
        filter(
            lambda x: hits_pct(x) <= HEALTH_THRESHOLD,
            list(
                API.NearestMobiles(
                    notoriety=[API.Notoriety.Ally, API.Notoriety.Innocent],  # pyright:ignore
                    maxDistance=range,
                )
            )
            + [API.Player],
        ),
        key=hits_pct,
    )

    if len(damaged) > 0:
        return damaged.pop()

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
    while not API.Player.IsDead:
        t = None
        API.CancelTarget()

        try:
            t = get_target()
        except Exception as e:
            p(f"e: {e}")
            continue

        s = get_spell(t)

        if not (t and s):
            API.Pause(0.1)
            continue

        API.CastSpell(s)
        if API.WaitForTarget("beneficial"):
            API.HeadMsg(f"Healing {t.Name}!", t)
            API.Target(t)  # pyright:ignore

        API.Pause(0.1)


main()
