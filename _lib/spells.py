from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import API

BASE_FCR = 1.5
BASE_CAST = 0.5
FCR_CAP = 6


class Spell:
    def __init__(self, name: str, base_cast_time: float, mana_cost: int):
        self.name = name
        self.base_cast_time = base_cast_time
        self.mana_cost = mana_cost

    @property
    def cost_lmc(self):
        return self.mana_cost * (API.Player.LowerManaCost / 100.0)

    def cast(self, target=None):
        if API.Player.Mana < self.cost_lmc:
            return

        API.CastSpell(self.name)
        if not target:
            return

        API.WaitForTarget()
        API.Target(target)  # pyright: ignore


def calculate_cast_time(base_cast_time, fc=None, fc_cap=2, min_cast_time=BASE_CAST):
    if fc is None:
        fc = min(API.Player.FasterCasting, fc_cap)
    else:
        fc = min(fc, fc_cap)

    return max(min_cast_time, base_cast_time - (fc * 0.25))


def calculate_recovery_time(fcr=None, base_recovery=BASE_FCR, fcr_cap=FCR_CAP):
    if fcr is None:
        fcr = min(API.Player.FasterCastRecovery, fcr_cap)
    else:
        fcr = min(fcr, fcr_cap)

    return max(0.0, base_recovery - (fcr * 0.25))


def calculate_full_spell_delay(
    base_cast_time,
    fc=None,
    fc_cap=2,
    fcr=None,
    base_recovery=BASE_FCR,
    fcr_cap=FCR_CAP,
    min_cast_time=BASE_CAST,
):
    cast_time = calculate_cast_time(base_cast_time, fc, fc_cap, min_cast_time)
    recovery = calculate_recovery_time(fcr, base_recovery, fcr_cap)
    return cast_time + recovery


def cast_spell_on_target(
    spell: Spell,
    target_serial: int,
    *,
    base_recovery: float = BASE_FCR,
    fcr_cap: int = FCR_CAP,
    target_timeout: float = 5,
) -> bool:
    if API.Player.Mana < spell.mana_cost:
        return False

    API.CastSpell(spell.name)

    if not API.WaitForTarget(timeout=target_timeout):
        return False

    API.Target(target_serial)  # type: ignore

    recovery = calculate_recovery_time(base_recovery=base_recovery, fcr_cap=fcr_cap)
    API.Pause(recovery)
    return True
