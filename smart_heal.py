"""Smart heal, targets player and any pets, cures poison if necessary, recasts if fizzled."""

import API
from _lib.utils import NOTORIETY_FRIENDLY


def _orange_petals():
    petals = API.FindType(0x1021, API.Backpack, hue=43)
    if not petals:
        return
    if not API.BuffExists("Poison Immunity"):
        API.UseObject(petals)


def _pets_by_health(range=10):
    mobiles = API.NearestMobiles(NOTORIETY_FRIENDLY, range)
    pets = [m for m in mobiles if m.IsRenamable and not m.IsDead]
    pets.sort(key=lambda m: m.HitsDiff)
    return pets


def _check_casting():
    API.ClearJournal()
    while not API.HasTarget():
        if API.InJournal("Your concentration is disturbed", True):
            return True
        API.Pause(0.05)
    return False


def _cast(spell, target=API.Player):
    if API.HasTarget():
        API.CancelTarget()
    API.CastSpell(spell)
    if _check_casting():
        _cast(spell, target)
    else:
        API.Target(target)  # pyright:ignore


def _get_player_spell():
    if API.Player.IsPoisoned:
        return "Arch Cure"
    elif API.Player.HitsDiff > 18:
        return "Greater Heal"
    elif API.Player.HitsDiff > 4:
        return "Heal"
    return None


def _get_pet_spell(pet):
    if pet.IsPoisoned:
        return "Arch Cure"
    elif pet.HitsDiff > 1:
        return "Greater Heal"
    return None


def run():
    _orange_petals()

    spell = _get_player_spell()
    if spell:
        return _cast(spell)

    for pet in _pets_by_health():
        spell = _get_pet_spell(pet)
        if spell:
            return _cast(spell, pet)


run()
