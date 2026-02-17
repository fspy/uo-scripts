"""Shared spell utilities for Legion scripts.

Provides helpers for calculating spell cast and recovery times based on Faster
Casting (FC) and Faster Cast Recovery (FCR) stats, plus common helpers for
casting targeted spells.

Note: API module is injected by Legion engine at runtime as a global.
Import is wrapped in try/except for type hints in editors.
"""

# pyright: basic

# Try to import API for type hints, but don't fail if unavailable
try:
    import API
except (ImportError, NameError):
    pass  # API is injected at runtime by Legion engine

# Default timing constants
DEFAULT_BASE_RECOVERY = 1.5
DEFAULT_MIN_CAST_TIME = 0.5
DEFAULT_FCR_CAP = 6


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


SPELL_CURE = Spell("Cure", 0.75, 6)
SPELL_ARCH_CURE = Spell("Arch Cure", 1.25, 11)
SPELL_GREATER_HEAL = Spell("Greater Heal", 1.25, 11)
SPELL_GIFT_OF_RENEWAL = Spell("Gift of Renewal", 3.0, 24)
SPELL_GIFT_OF_LIFE = Spell("Gift of Life", 4.0, 70)

SELF_POISON_PATTERNS: "list[tuple[str, int]]" = [
    ("you are in extreme pain, and require immediate aid!", 5),
    ("you feel extremely weak and are in severe pain!", 4),
    ("you begin to feel pain throughout your body!", 3),
    ("you feel disorientated and nauseous!", 2),
    ("you feel a bit nauseous", 1),
]
POISON_PATTERNS: "list[tuple[str, int]]" = [
    ("begins to spasm uncontrollably", 5),  # Lethal
    ("is wracked with extreme pain", 4),  # Deadly
    ("stumbles around in confusion", 3),  # Greater
    ("looks extremely ill", 2),  # Standard
    ("looks ill", 1),  # Lesser
]


def calculate_cast_time(
    base_cast_time, fc=None, fc_cap=2, min_cast_time=DEFAULT_MIN_CAST_TIME
):
    """
    Calculate actual spell cast time based on Faster Casting (FC).

    FC reduces cast time by 0.25s per level, with school-specific caps:
    - Magery/Necromancy: cap at FC 2
    - Spellweaving/Chivalry: cap at FC 4

    Args:
        base_cast_time: Base casting time in seconds
        fc: Faster Casting value (defaults to player's current FC)
        fc_cap: School-specific FC cap (default 2)
        min_cast_time: Minimum cast time floor (default 0.5s)

    Returns:
        Actual cast time in seconds

    Example:
        # Magery Greater Heal (1.25s base, FC cap 2)
        cast_time = calculate_cast_time(1.25, fc_cap=2)
    """
    if fc is None:
        fc = min(API.Player.FasterCasting, fc_cap)
    else:
        fc = min(fc, fc_cap)

    return max(min_cast_time, base_cast_time - (fc * 0.25))


def calculate_recovery_time(
    fcr=None, base_recovery=DEFAULT_BASE_RECOVERY, fcr_cap=DEFAULT_FCR_CAP
):
    """
    Calculate spell recovery time based on Faster Cast Recovery (FCR).

    FCR reduces recovery by 0.25s per level, capping at FCR 6.

    IMPORTANT: Use this AFTER WaitForTarget() completes, since the cast time
    is already consumed while waiting for the target cursor to appear.

    Args:
        fcr: Faster Cast Recovery value (defaults to player's current FCR)
        base_recovery: Base recovery time in seconds (default 1.5s)
        fcr_cap: FCR cap (default 6)

    Returns:
        Actual recovery time in seconds (minimum 0.0)

    Example:
        # After casting targeted spell:
        API.CastSpell("Greater Heal")
        if API.WaitForTarget(timeout=5):  # Cast time consumed here
            API.Target(pet.Serial)
            recovery = calculate_recovery_time()
            API.Pause(recovery)  # Only wait for recovery
    """
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
    base_recovery=DEFAULT_BASE_RECOVERY,
    fcr_cap=DEFAULT_FCR_CAP,
    min_cast_time=DEFAULT_MIN_CAST_TIME,
):
    """
    Calculate full spell delay (cast + recovery) for non-targeted spells.

    Use this for spells that don't have a target cursor (e.g., area effects,
    self-buffs without targeting). For targeted spells, use calculate_recovery_time()
    after WaitForTarget() completes.

    Args:
        base_cast_time: Base casting time in seconds
        fc: Faster Casting value (defaults to player's current FC)
        fc_cap: School-specific FC cap (default 2)
        fcr: Faster Cast Recovery value (defaults to player's current FCR)
        base_recovery: Base recovery time in seconds (default 1.5s)
        fcr_cap: FCR cap (default 6)
        min_cast_time: Minimum cast time floor (default 0.5s)

    Returns:
        Total delay in seconds (cast + recovery)

    Example:
        # Non-targeted spell like Earthquake
        API.CastSpell("Earthquake")
        delay = calculate_full_spell_delay(2.25, fc_cap=2)
        API.Pause(delay)
    """
    cast_time = calculate_cast_time(base_cast_time, fc, fc_cap, min_cast_time)
    recovery = calculate_recovery_time(fcr, base_recovery, fcr_cap)
    return cast_time + recovery


def cast_spell_on_target(
    spell: Spell,
    target_serial: int,
    *,
    base_recovery: float = DEFAULT_BASE_RECOVERY,
    fcr_cap: int = DEFAULT_FCR_CAP,
    target_timeout: float = 5,
) -> bool:
    """Cast a targeted spell using the standard targeting sequence.

    Notes:
    - This intentionally does not use API.PreTarget().
    - WaitForTarget() consumes the cast time; we only pause for recovery.

    Returns:
        True if target cursor appeared and we targeted; False otherwise.
    """
    if API.Player.Mana < spell.mana_cost:
        return False

    API.CastSpell(spell.name)

    if not API.WaitForTarget(timeout=target_timeout):
        return False

    API.Target(target_serial)  # type: ignore

    recovery = calculate_recovery_time(base_recovery=base_recovery, fcr_cap=fcr_cap)
    API.Pause(recovery)
    return True
