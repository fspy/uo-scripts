import time

import API
from _lib.utils import Hue, h, p

enemy_of_one = True
divine_fury = False
consecrate_weapon = True
momentum_strike = True

counter_attack = True
evasion = 0.5
confidence = False
remove_curse = ("Blood Oath",)

honor_targets = False
onslaught = True
trapped_box = 0x40358F00
default_pause = 0.2

MEGA_AGGRO = True


def mobs_list(maxDistance=8):
    return API.NearestMobiles(
        [
            API.Notoriety.Criminal,
            API.Notoriety.Enemy,
            API.Notoriety.Gray,
            API.Notoriety.Murderer,
        ],  # pyright:ignore
        maxDistance,
    )


def weapon_name():
    weapon = API.FindLayer("TwoHanded") or API.FindLayer("OneHanded")
    if not weapon:
        return ""
    props = API.ItemNameAndProps(weapon.Serial, True).split("\n")
    return props[0].strip().lower()


def mana_check(spell):
    cost = mana_costs[spell]
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
    "Onslaught": 20,
}


def decurse():
    if not remove_curse:
        return

    global apple_timer
    for curse in remove_curse:
        if not API.BuffExists(curse):
            continue

        if (
            API.FindType(0x2FD8, API.Backpack, hue=1160)
            and time.time() - apple_timer > 30
        ):
            API.UseObject(API.Found)
            return

        retries = 3
        while retries:
            API.CastSpell("Remove Curse")
            if API.WaitForTarget("beneficial"):
                API.TargetSelf()
                API.Pause(default_pause)
            retries -= 1


def paralyze():
    if not trapped_box:
        return

    if API.FindItem(trapped_box) and API.BuffExists("Paralyze"):
        API.UseObject(API.Found, True)
        API.Pause(default_pause)


def honor(enemy):
    global current

    if honor_targets and enemy.Serial not in current:
        API.Virtue("Honor")
        API.WaitForTarget(timeout=1)
        API.Target(enemy)  # pyright:ignore
        API.Pause(default_pause)
        if API.InJournalAny(["Honorable Combat", "cannot honor this monster"], True):
            current.append(enemy.Serial)


def fighting(focus, targets):
    global onslaught_timer
    API.Attack(focus)

    buffs = [  # spell name, enabled, buff name
        ("Enemy of One", enemy_of_one, None),
        ("Divine Fury", divine_fury, None),
        ("Consecrate Weapon", consecrate_weapon, "Consecrate"),
    ]

    for spell_name, enabled, buff_name in buffs:
        buff_name = buff_name or spell_name
        if enabled and not API.BuffExists(buff_name) and mana_check(spell_name):
            API.CastSpell(spell_name)
            API.Pause(default_pause)

    has_defensive = any(
        API.BuffExists(defensive)
        for defensive in ["Counter Attack", "Evasion", "Confidence"]
    )
    if not has_defensive:
        hp_ratio = API.Player.Hits / API.Player.HitsMax
        if confidence and hp_ratio < confidence and mana_check("Confidence"):
            API.CastSpell("Confidence")
        elif evasion and hp_ratio < evasion and mana_check("Evasion"):
            API.CastSpell("Evasion")
        elif counter_attack and mana_check("Counter Attack"):
            API.CastSpell("Counter Attack")

    weapon = weapon_name()
    is_double_axe = "double axe" in weapon

    if targets > 2:
        if is_double_axe:
            if not API.SecondaryAbilityActive() and mana_check("Whirlwind Attack"):
                API.ToggleAbility("Secondary")
        elif (
            momentum_strike
            and not API.BuffExists("Momentum Strike")
            and mana_check("Momentum Strike")
        ):
            API.CastSpell("Momentum Strike")

    elif targets == 2:
        if (
            momentum_strike
            and not API.BuffExists("Momentum Strike")
            and mana_check("Momentum Strike")
        ):
            API.CastSpell("Momentum Strike")

    else:
        if is_double_axe:
            if (
                onslaught
                and time.time() - onslaught_timer > 3
                and mana_check("Onslaught")
            ):
                onslaught_timer = time.time()
                API.CastSpell("Onslaught")

            elif (
                not API.PrimaryAbilityActive()
                and mana_check("Double Strike")
                and time.time() - onslaught_timer <= 3
            ):
                API.ToggleAbility("Primary")

        elif (
            "bladed staff" in weapon
            and not API.PrimaryAbilityActive()
            and mana_check("Armor Ignore")
        ):
            API.ToggleAbility("Primary")

    if API.InJournal("deliver an onslaught of sword strikes"):
        onslaught_timer = time.time()
        API.ClearJournal()


current = []
onslaught_timer = time.time()
apple_timer = time.time()

while not API.StopRequested:
    if API.Player.IsDead or API.Player.IsHidden:
        API.Pause(default_pause)
        continue

    enemies = mobs_list()
    if len(enemies) == 0:
        API.Pause(default_pause)
        continue

    paralyze()
    decurse()
    honor(enemies[0])

    if MEGA_AGGRO:
        for e in enemies:
            if e.Serial not in current:
                API.Attack(e)
                current.append(e.Serial)
                API.Pause(default_pause)

    while API.FindMobile(enemies[0]) and enemies[0].Distance < 2:
        fighting(enemies[0], len(mobs_list(1)))
        API.Pause(default_pause)

    API.CancelTarget()
    if len(current) > 20:
        current = current[-20:]
