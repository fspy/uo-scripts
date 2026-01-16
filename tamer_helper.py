import re
import time

import API
from _lib.spells import (
    SPELL_ARCH_CURE,
    SPELL_CURE,
    SPELL_GIFT_OF_LIFE,
    SPELL_GIFT_OF_RENEWAL,
    SPELL_GREATER_HEAL,
    cast_spell_on_target,
    detect_poison_level,
)

MAX_PET_RANGE = 12
HEAL_THRESHOLD = 0.70
HEAL_UNTIL = 0.95
RENEWAL_THRESHOLD = 0.90
CHECK_INTERVAL = 0.05

ARCANE_FOCUS_GRAPHIC = 0x3155
BASE_RECOVERY = 1.5
FCR_CAP = 6


class PetState:
    def __init__(self):
        self.gift_of_life_expires_at = 0.0
        self.gift_of_renewal_expires_at = 0.0
        self.was_dead = False


pet_states = {}


def get_pet_state(pet_serial):
    state = pet_states.get(pet_serial)
    if state is None:
        state = PetState()
        pet_states[pet_serial] = state
    return state


cached_gol_duration = None
cached_gor_recast_time = None


def get_arcane_focus_level():
    focus = API.FindType(ARCANE_FOCUS_GRAPHIC, API.Player.Backpack)
    if not focus:
        return 0

    props = focus.NameAndProps(wait=True, timeout=5)
    if not props:
        return 0

    match = re.search(r"Strength\s+Bonus\s+(\d+)", props, re.IGNORECASE)
    if match:
        return int(match.group(1))

    return 0


def validate_arcane_focus():
    global cached_gol_duration, cached_gor_recast_time

    focus_level = get_arcane_focus_level()
    if focus_level == 0:
        API.SysMsg("[Tamer Helper] No Arcane Focus, aborting.", 32)
        return None

    spellweaving_skill = API.GetSkill("Spellweaving").Value
    gol_duration = (max(1.0, (spellweaving_skill * 10) / 120) + focus_level) * 60
    gor_recast_time = 30 + (focus_level * 10) + 65

    cached_gol_duration = gol_duration
    cached_gor_recast_time = gor_recast_time

    return focus_level


def get_hp_percent(mobile):
    return 1.0 if mobile.HitsMax <= 0 else mobile.Hits / mobile.HitsMax


def find_my_pets(max_distance=12):
    pets = []
    all_mobiles = API.GetAllMobiles(distance=max_distance)

    for mobile in all_mobiles:
        if hasattr(mobile, "IsRenamable") and mobile.IsRenamable:
            if mobile.Distance <= max_distance:
                pets.append(mobile)

    pets.sort(key=lambda p: get_hp_percent(p))

    return pets


def cure_pet(pet, poison_level):
    spell_info = SPELL_ARCH_CURE if poison_level >= 4 else SPELL_CURE

    return cast_spell_on_target(spell_info, pet.Serial)


def heal_pet(pet):
    if pet.IsYellowHits:
        return False

    return cast_spell_on_target(SPELL_GREATER_HEAL, pet.Serial)


def needs_gift_of_life(pet):
    now = time.time()
    state = get_pet_state(pet.Serial)

    if state.was_dead and not pet.IsDead:
        state.was_dead = False
        state.gift_of_life_expires_at = 0
        state.gift_of_renewal_expires_at = 0
        return True

    state.was_dead = pet.IsDead

    return now >= state.gift_of_life_expires_at


def cast_gift_of_life(pet):
    success = cast_spell_on_target(SPELL_GIFT_OF_LIFE, pet.Serial)

    if success and not API.InJournal("your concentration is disturbed"):
        duration = cached_gol_duration if cached_gol_duration else 180  # Fallback 3 min
        state = get_pet_state(pet.Serial)
        state.gift_of_life_expires_at = time.time() + duration
        API.CreateCooldownBar(duration, "Gift of Life", 63)
        return True

    return False


def can_apply_renewal(pet):
    if pet.IsPoisoned:
        return False

    now = time.time()
    state = get_pet_state(pet.Serial)
    return now >= state.gift_of_renewal_expires_at


def cast_gift_of_renewal(pet):
    success = cast_spell_on_target(SPELL_GIFT_OF_RENEWAL, pet.Serial)

    if success and not API.InJournal("your concentration is disturbed"):
        recast_time = cached_gor_recast_time if cached_gor_recast_time else 90
        state = get_pet_state(pet.Serial)
        state.gift_of_renewal_expires_at = time.time() + recast_time
        API.CreateCooldownBar(recast_time, "Gift of Renewal", 53)
        return True

    return False


def main_loop():
    focus_level = validate_arcane_focus()
    if focus_level is None:
        return

    API.ClearJournal()
    while not API.StopRequested:
        pets = find_my_pets(MAX_PET_RANGE)

        for pet in pets:
            if pet.IsDead:
                continue

            if pet.IsPoisoned:
                poison_level = detect_poison_level(pet.Name)
                cure_pet(pet, poison_level)
                API.Pause(0.3)
                continue

            hp_pct = get_hp_percent(pet)
            if hp_pct < HEAL_THRESHOLD and not pet.IsYellowHits:
                while get_hp_percent(pet) < HEAL_UNTIL and not API.StopRequested:
                    pet = API.FindMobile(pet.Serial)
                    if not pet or pet.IsDead or pet.IsPoisoned or pet.IsYellowHits:
                        break
                    heal_pet(pet)
                continue

            if hp_pct < RENEWAL_THRESHOLD and can_apply_renewal(pet):
                cast_gift_of_renewal(pet)

            if needs_gift_of_life(pet):
                cast_gift_of_life(pet)

        API.Pause(CHECK_INTERVAL)


main_loop()
