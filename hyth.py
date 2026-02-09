import API
from _lib.utils import h, p

RANGE = 16


def find_baddies():
    mobs = API.NearestMobiles(
        [
            API.Notoriety.Criminal,
            API.Notoriety.Enemy,
            API.Notoriety.Gray,
            API.Notoriety.Murderer,
        ],  # pyright:ignore
        RANGE,
    )

    return filter(lambda m: m.HasLineOfSightFrom(), mobs)


def has_players_nearby():
    mobs = API.NearestMobiles([API.Notoriety.Ally, API.Notoriety.Innocent], RANGE)
    filtered = filter(
        lambda player: player.Serial == API.Player.Serial or not player.IsRenamable,
        mobs,
    )
    if len(list(filtered)) > 0:
        p(list(filtered))
    return any(filtered)


ignored = []
while not API.StopRequested:
    if has_players_nearby():
        h("players nearby, waiting")
        API.Pause(1)
        continue

    while not API.Player.IsHidden:
        API.Pause(0.1)

    for baddie in find_baddies():
        if baddie.Serial in ignored:
            continue

        ignored.append(baddie.Serial)
        h("Attacking", baddie)
        API.Attack(baddie)
        API.Pause(0.1)

    if API.Player.InWarMode:
        API.Pause(0.1)
        API.SetWarMode(False)

    API.Pause(1)
