import API

enemy_of_one = True
divine_fury = False
consecrate_weapon = True
momentum_strike = True

counter_attack = True
evasion = True, 0.7
confidence = False, 0.3
remove_curse = True, ["Blood Oath"]

honor = True

default_pause = 0.2


def mobs_list(maxDistance=8):
    return API.NearestMobiles(
        [
            API.Notoriety.Criminal,
            API.Notoriety.Enemy,
            API.Notoriety.Gray,
            API.Notoriety.Murderer,
        ],
        maxDistance,
    )


def weapon_name():
    weapon = API.FindLayer("TwoHanded") or API.FindLayer("OneHanded")
    if not weapon:
        return ""
    props = API.ItemNameAndProps(weapon.Serial, True).split("\n")
    return props[0].strip().lower()


def _mana_check(cost):
    return API.Player.Mana >= cost * (API.Player.LowerManaCost / 100.0)


mana_costs = {
    "Enemy of One": 20,
    "Divine Fury": 10,
    "Consecrate Weapon": 10,
    "Momentum Strike": 10,
    "Counter Attack": 5,
    "Evasion": 10,
    "Confidence": 10,
    "Armor Ignore": 30,
    "Double Strike": 30,
    "Whirlwind Attack": 15,
}


def fighting(focus, targets):
    API.Attack(focus)

    if (
        enemy_of_one
        and not API.BuffExists("Enemy of One")
        and _mana_check(mana_costs["Enemy of One"])
    ):
        API.CastSpell("Enemy of One")
        API.Pause(default_pause)

    if (
        divine_fury
        and not API.BuffExists("Divine Fury")
        and _mana_check(mana_costs["Divine Fury"])
    ):
        API.CastSpell("Divine Fury")
        API.Pause(default_pause)

    if (
        consecrate_weapon
        and not API.BuffExists("Consecrate")
        and _mana_check(mana_costs["Consecrate Weapon"])
    ):
        API.CastSpell("Consecrate Weapon")
        API.Pause(default_pause)

    if (
        counter_attack
        and not API.BuffExists("Counter Attack")
        and not API.BuffExists("Evasion")
        and not API.BuffExists("Confidence")
        and _mana_check(mana_costs["Counter Attack"])
    ):
        API.CastSpell("Counter Attack")
        API.Pause(default_pause)

    if (
        evasion
        and not API.BuffExists("Counter Attack")
        and not API.BuffExists("Evasion")
        and not API.BuffExists("Confidence")
        and _mana_check(mana_costs["Evasion"])
        and API.Player.Hits / API.Player.HitsMax < evasion[1]
    ):
        API.CastSpell("Evasion")
        API.Pause(default_pause)

    if (
        confidence
        and not API.BuffExists("Counter Attack")
        and not API.BuffExists("Evasion")
        and not API.BuffExists("Confidence")
        and _mana_check(mana_costs["Confidence"])
        and API.Player.Hits / API.Player.HitsMax < confidence[1]
    ):
        API.CastSpell("Confidence")
        API.Pause(default_pause)

    if targets > 2:
        if "double axe" in weapon_name():
            if not API.SecondaryAbilityActive() and _mana_check(
                mana_costs["Whirlwind Attack"]
            ):
                API.ToggleAbility("Secondary")
        elif (
            momentum_strike
            and not API.BuffExists("Momentum Strike")
            and _mana_check(mana_costs["Momentum Strike"])
        ):
            API.CastSpell("Momentum Strike")
            API.Pause(default_pause)

    elif targets == 2:
        if (
            momentum_strike
            and not API.BuffExists("Momentum Strike")
            and _mana_check(mana_costs["Momentum Strike"])
        ):
            API.CastSpell("Momentum Strike")
            API.Pause(default_pause)

    else:
        if not API.PrimaryAbilityActive():
            if (
                "double axe" in weapon_name()
                and _mana_check(mana_costs["Double Strike"])
            ) or (
                "bladed staff" in weapon_name()
                and _mana_check(mana_costs["Armor Ignore"])
            ):
                API.ToggleAbility("Primary")


current = []
while not API.StopRequested:
    if API.Player.IsDead or API.Player.IsHidden:
        API.Pause(1)
        continue

    enemies = mobs_list()
    if len(enemies) < 1:
        API.Pause(default_pause)
        continue

    if honor:
        for enemy in enemies:
            if enemy.Serial in current:
                continue
            API.Virtue("Honor")
            API.WaitForTarget(timeout=1)
            API.Target(enemy)  # pyright:ignore
            API.Pause(default_pause)
            if API.InJournal("Honorable", True):
                current.append(enemy.Serial)

    while API.FindMobile(enemies[0]) and enemies[0].Distance < 2:
        fighting(enemies[0], len(mobs_list(1)))
        API.Pause(default_pause)

    # clean up
    if len(current) > 100:
        current = []
