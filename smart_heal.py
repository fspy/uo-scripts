import API
from _lib.spells import detect_poison_level, detect_self_poison_level

heal_pet_threshold = 0.9


def p(m, c=1150):
    API.SysMsg(m, c)


if API.HasTarget("beneficial"):
    API.Stop()
elif API.HasTarget("any"):
    API.CancelTarget()


def health_percent(mobile) -> float:
    if mobile.HitsMax <= 0:
        return 1.0
    return mobile.Hits / mobile.HitsMax


def find_my_pets(max_distance=10):
    return sorted(
        [
            m
            for m in API.NearestMobiles(
                [
                    API.Notoriety.Innocent,
                    API.Notoriety.Ally,
                    API.Notoriety.Gray,
                ],
                max_distance,
            )
            if m.IsRenamable and not m.IsDead
        ],
        key=health_percent,
    )


def get_player_heal_spell():
    if API.Player.IsPoisoned:
        if detect_self_poison_level() > 3:
            return "Arch Cure"
        return "Cure"
    if API.Player.HitsDiff > 15:
        return "Greater Heal"
    elif API.Player.HitsDiff > 4:
        return "Heal"
    return None


def get_pet_heal_spell(pet, threshold=0.7):
    if pet.IsPoisoned:
        if detect_poison_level(pet.Name) > 3:
            return "Arch Cure"
        return "Cure"
    if health_percent(pet) < threshold:
        return "Greater Heal"
    return None


def select_heal_target():
    spell = get_player_heal_spell()
    if spell:
        return API.Player.Serial, spell

    for pet in find_my_pets():
        spell = get_pet_heal_spell(pet, heal_pet_threshold)
        if spell:
            return pet.Serial, spell

    return None, None


target_serial, spell = select_heal_target()
if target_serial and spell:
    API.PreTarget(target_serial, "beneficial")
    API.CastSpell(spell)
