"""
Tamer Helper - Pet Monitoring & Healing Script

Continuously monitors pets within range for:
- Poison (detects level 1-5 via journal, cures with appropriate spell)
- Health deficit (heals with Greater Heal until >95%)
- Mortal Strike (skips healing when detected)
- Gift of Life maintenance (auto-rez safety net)
- Gift of Renewal maintenance (HoT when hurt)

Priority Order:
0. Gift of Life - maintain always (reapply on expiry/resurrection)
1. Cure poison - immediate threat
2. Heal - if hurt and not mortaled
3. Gift of Renewal - HoT for sustained healing

USAGE: Run inside TazUO client. Script auto-starts monitoring on login.
"""

import re
import time

import API
from lib.spells import calculate_recovery_time

# =============================================================================
# CONFIGURATION
# =============================================================================

MAX_PET_RANGE = 12  # Monitor pets within this many tiles
HEAL_THRESHOLD = 0.70  # Start healing below 70% HP
HEAL_UNTIL = 0.95  # Keep healing until above 95% HP
RENEWAL_THRESHOLD = 0.90  # Apply Gift of Renewal below 90% HP
CHECK_INTERVAL = 0.05  # Seconds between main loop iterations

# Arcane Focus
ARCANE_FOCUS_GRAPHIC = 0x3155  # Arcane focus crystal graphic ID

# Spell definitions: (name, base_cast_time, mana_cost)
SPELL_CURE = ("Cure", 0.75, 6)
SPELL_ARCH_CURE = ("Arch Cure", 1.25, 11)
SPELL_GREATER_HEAL = ("Greater Heal", 1.25, 11)
SPELL_GIFT_OF_RENEWAL = ("Gift of Renewal", 3.0, 24)
SPELL_GIFT_OF_LIFE = ("Gift of Life", 4.0, 70)

# Spell timing constants
BASE_RECOVERY = 1.5  # Recovery time between spells
MAGERY_FC_CAP = 2
SPELLWEAVING_FC_CAP = 4
FCR_CAP = 6

# Poison detection patterns (journal messages when others are poisoned)
# Format: (pattern, poison_level)
POISON_PATTERNS = [
    ("begins to spasm uncontrollably", 5),  # Lethal
    ("is wracked with extreme pain", 4),  # Deadly
    ("stumbles around in confusion", 3),  # Greater
    ("looks extremely ill", 2),  # Standard
    ("looks ill", 1),  # Lesser
]


# =============================================================================
# GLOBAL STATE
# =============================================================================

# Track Gift of Life timers per pet: {pet_serial: expiry_timestamp}
gift_of_life_timers = {}
# Track pet death state to detect resurrections: {pet_serial: was_dead}
pet_was_dead = {}
# Track Gift of Renewal timers per pet: {pet_serial: expiry_timestamp}
gift_of_renewal_timers = {}

# Cached values (set at startup, don't re-check)
cached_focus_level = None
cached_spellweaving_skill = None
cached_gol_duration = None
cached_gor_recast_time = None


# =============================================================================
# ARCANE FOCUS DETECTION & DURATION CALCULATION
# =============================================================================


def get_arcane_focus_level():
    """
    Find arcane focus in backpack and parse its strength level from tooltip.

    Returns:
        int: Focus level (1-6), or 0 if no focus found
    """
    focus = API.FindType(ARCANE_FOCUS_GRAPHIC, API.Player.Backpack)
    if not focus:
        return 0

    # Get tooltip text
    props = focus.NameAndProps(wait=True, timeout=5)
    if not props:
        return 0

    # Parse "Strength Bonus N" from tooltip
    match = re.search(r"Strength\s+Bonus\s+(\d+)", props, re.IGNORECASE)
    if match:
        return int(match.group(1))

    return 0


def calculate_gift_of_life_duration(focus_level, spellweaving_skill):
    """
    Calculate Gift of Life duration in seconds.

    Formula from UOGuide:
    - Base: (Spellweaving x 10) / 120 minutes, minimum 1
    - Bonus: +1 minute per focus level
    - Penalty: -1 minute if no focus (focus_level = 0)

    Args:
        focus_level: Arcane focus strength (0-6)
        spellweaving_skill: Spellweaving skill value

    Returns:
        Duration in seconds
    """
    # Base duration: (skill x 10) / 120, minimum 1 minute
    base_minutes = max(1.0, (spellweaving_skill * 10) / 120)

    # Add focus bonus (or -1 penalty if no focus)
    if focus_level > 0:
        total_minutes = base_minutes + focus_level
    else:
        total_minutes = max(1.0, base_minutes - 1)  # -1 penalty, minimum 1

    return total_minutes * 60  # Convert to seconds


def calculate_gift_of_renewal_recast_time(focus_level):
    """
    Calculate Gift of Renewal total recast time (duration + cooldown).

    Duration: 30 + (focus_level * 10) seconds
    Cooldown: 60 seconds (fixed)
    Total: duration + 60

    Args:
        focus_level: Arcane focus strength (0-6)

    Returns:
        Total time in seconds before recast is allowed
    """
    duration = 30 + (focus_level * 10)
    cooldown = 60
    return duration + cooldown


def validate_arcane_focus():
    """
    Check for arcane focus at startup. STOP SCRIPT if missing (very clear).

    Returns:
        int: Focus level (1-6), or None if missing (stops script)
    """
    global cached_focus_level, cached_spellweaving_skill
    global cached_gol_duration, cached_gor_recast_time

    # Get focus level
    focus_level = get_arcane_focus_level()

    if focus_level == 0:
        API.SysMsg("=" * 50, 32)
        API.SysMsg("ERROR: NO ARCANE FOCUS FOUND IN BACKPACK!", 32)
        API.SysMsg("", 32)
        API.SysMsg("You must have an Arcane Focus to run this script.", 32)
        API.SysMsg("Cast Arcane Circle on an Arcane Circle item to create one.", 32)
        API.SysMsg("", 32)
        API.SysMsg("SCRIPT STOPPED - Obtain an Arcane Focus and restart.", 32)
        API.SysMsg("=" * 50, 32)
        return None  # Signal to stop

    # Get spellweaving skill
    spellweaving_skill = API.GetSkill("Spellweaving").Value

    # Calculate durations
    gol_duration = calculate_gift_of_life_duration(focus_level, spellweaving_skill)
    gor_recast_time = calculate_gift_of_renewal_recast_time(focus_level)

    # Cache values
    cached_focus_level = focus_level
    cached_spellweaving_skill = spellweaving_skill
    cached_gol_duration = gol_duration
    cached_gor_recast_time = gor_recast_time

    # Display info
    API.SysMsg("=" * 50, 66)
    API.SysMsg(f"Arcane Focus detected - Strength Bonus {focus_level}", 66)
    API.SysMsg(f"Spellweaving Skill: {spellweaving_skill:.1f}", 66)
    API.SysMsg(f"Gift of Life duration: {gol_duration / 60:.1f} minutes", 66)
    API.SysMsg(f"Gift of Renewal recast time: {gor_recast_time} seconds", 66)
    API.SysMsg("=" * 50, 66)

    return focus_level


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_hp_percent(mobile):
    """Get health percentage (0.0 to 1.0)."""
    if mobile.HitsMax <= 0:
        return 1.0
    return mobile.Hits / mobile.HitsMax


def find_my_pets(max_distance=12):
    """
    Find all owned pets/followers within range.

    Returns:
        List of PyMobile objects, sorted by HP% (lowest first)
    """
    pets = []
    all_mobiles = API.GetAllMobiles(distance=max_distance)

    for mobile in all_mobiles:
        # Filter for followers (pets/summons owned by player)
        # IsRenamable is a good indicator of owned pets
        if hasattr(mobile, "IsRenamable") and mobile.IsRenamable:
            if mobile.Distance <= max_distance:
                pets.append(mobile)

    # Sort by HP percentage (lowest first for healing priority)
    pets.sort(key=lambda p: get_hp_percent(p))

    return pets


def check_spell_fizzled():
    """Check if last spell fizzled by looking in journal."""
    return API.InJournal("your concentration is disturbed")


# =============================================================================
# POISON DETECTION & CURE
# =============================================================================


def detect_poison_level(pet_name):
    """
    Check journal for poison level message.

    Args:
        pet_name: Name of the pet to check

    Returns:
        Poison level 0-5 (0 = unknown/none, 1-5 = poison levels)
    """
    # Check patterns in order of severity (most severe first)
    for pattern, level in POISON_PATTERNS:
        if API.InJournal(f"* {pet_name} {pattern}"):
            return level

    # No poison message found, default to unknown (will use regular Cure)
    return 0


def cure_pet(pet, poison_level):
    """
    Cure poisoned pet using appropriate spell based on poison level.

    Args:
        pet: PyMobile object
        poison_level: Poison level 0-5 (4-5 uses Arch Cure, else Cure)

    Returns:
        True if cure was attempted, False on failure
    """
    # Use Arch Cure for Deadly (4) and Lethal (5) poison
    spell_info = SPELL_ARCH_CURE if poison_level >= 4 else SPELL_CURE

    return cast_spell_on_target(spell_info, pet.Serial)


# =============================================================================
# HEALING
# =============================================================================


def heal_pet(pet):
    """
    Cast Greater Heal on pet.

    Args:
        pet: PyMobile object

    Returns:
        True if heal was attempted, False on failure
    """
    # Don't heal if pet is mortaled (yellow hits)
    if pet.IsYellowHits:
        return False

    return cast_spell_on_target(SPELL_GREATER_HEAL, pet.Serial)


# =============================================================================
# GIFT OF LIFE (Auto-Rez Safety Net)
# =============================================================================


def needs_gift_of_life(pet):
    """
    Check if pet needs Gift of Life applied.

    Triggers:
    - Timer expired
    - Pet was just resurrected (buff consumed)

    Args:
        pet: PyMobile object

    Returns:
        True if Gift of Life should be cast
    """
    now = time.time()

    # Check if pet was just resurrected (was dead, now alive)
    was_dead = pet_was_dead.get(pet.Serial, False)
    is_alive = not pet.IsDead

    if was_dead and is_alive:
        # Pet was resurrected! GoL was consumed, needs reapplication
        pet_was_dead[pet.Serial] = False
        gift_of_life_timers[pet.Serial] = 0  # Clear GoL timer
        gift_of_renewal_timers[pet.Serial] = (
            0  # Clear GoR timer (death resets cooldown)
        )
        return True

    # Update death tracking
    pet_was_dead[pet.Serial] = pet.IsDead

    # Check if timer expired
    expiry = gift_of_life_timers.get(pet.Serial, 0)
    return now >= expiry


def cast_gift_of_life(pet):
    """
    Cast Gift of Life on pet and track timer on success.

    Args:
        pet: PyMobile object

    Returns:
        True if cast was successful
    """
    success = cast_spell_on_target(SPELL_GIFT_OF_LIFE, pet.Serial)

    if success and not check_spell_fizzled():
        # Mark timer using cached duration (guaranteed set by validate_arcane_focus)
        duration = cached_gol_duration if cached_gol_duration else 180  # Fallback 3 min
        gift_of_life_timers[pet.Serial] = time.time() + duration
        # Show cooldown bar (light green)
        API.CreateCooldownBar(duration, "Gift of Life", 63)
        return True

    return False


# =============================================================================
# GIFT OF RENEWAL (HoT)
# =============================================================================


def can_apply_renewal(pet):
    """
    Check if Gift of Renewal can be cast on pet.

    Conditions:
    - Pet is not poisoned (would waste spell - cures then ends)
    - Timer has expired

    Args:
        pet: PyMobile object

    Returns:
        True if Gift of Renewal should be cast
    """
    # Cannot cast on poisoned pet (wastes the HoT effect)
    if pet.IsPoisoned:
        return False

    # Check if timer expired
    now = time.time()
    expiry = gift_of_renewal_timers.get(pet.Serial, 0)
    return now >= expiry


def cast_gift_of_renewal(pet):
    """
    Cast Gift of Renewal on pet and track timer on success.

    Args:
        pet: PyMobile object

    Returns:
        True if cast was successful
    """
    success = cast_spell_on_target(SPELL_GIFT_OF_RENEWAL, pet.Serial)

    if success and not check_spell_fizzled():
        # Mark timer using cached recast time (guaranteed set by validate_arcane_focus)
        recast_time = (
            cached_gor_recast_time if cached_gor_recast_time else 90
        )  # Fallback 90 sec
        gift_of_renewal_timers[pet.Serial] = time.time() + recast_time
        # Show cooldown bar (light yellow)
        API.CreateCooldownBar(recast_time, "Gift of Renewal", 53)
        return True

    return False


# =============================================================================
# SPELL CASTING
# =============================================================================


def cast_spell_on_target(spell_info, target_serial):
    """
    Cast spell using proper targeting sequence (no PreTarget).

    Args:
        spell_info: Tuple of (spell_name, base_cast_time, mana_cost)
        target_serial: Serial number of target
        fc_cap: Faster Casting cap for this spell school (not used, kept for compatibility)

    Returns:
        True if spell was cast and target cursor appeared, False otherwise
    """
    spell_name, _, mana_cost = spell_info

    # Check if we have enough mana (optional - could wait/meditate)
    if API.Player.Mana < mana_cost:
        return False

    # Cast spell
    API.CastSpell(spell_name)

    # Wait for target cursor (this blocks through cast time)
    if not API.WaitForTarget(timeout=5):
        return False

    # Target the pet
    API.Target(target_serial)  # type: ignore

    # Only wait for recovery time (cast time already consumed by WaitForTarget)
    recovery = calculate_recovery_time(base_recovery=BASE_RECOVERY, fcr_cap=FCR_CAP)
    API.Pause(recovery)

    return True


# =============================================================================
# MAIN LOOP
# =============================================================================


def main_loop():
    """
    Main monitoring loop with priority-based pet care.

    Priority Order:
    0. Gift of Life - maintain always
    1. Cure poison - immediate threat
    2. Heal - if hurt and not mortaled
    3. Gift of Renewal - HoT when hurt
    """
    # Validate arcane focus at startup
    focus_level = validate_arcane_focus()
    if focus_level is None:
        # No focus found - script stopped with clear error message
        return

    # Clear journal at start
    API.ClearJournal()

    API.SysMsg("Tamer Helper started - monitoring pets", 66)

    while not API.StopRequested:
        # Find all pets in range (sorted by HP, lowest first)
        pets = find_my_pets(MAX_PET_RANGE)

        for pet in pets:
            # Skip dead pets
            if pet.IsDead:
                continue

            hp_pct = get_hp_percent(pet)

            # PRIORITY 0: Gift of Life - ALWAYS maintain
            if needs_gift_of_life(pet):
                cast_gift_of_life(pet)
                # Don't skip other priorities - check them too

            # PRIORITY 1: Cure poison immediately
            if pet.IsPoisoned:
                poison_level = detect_poison_level(pet.Name)
                cure_pet(pet, poison_level)
                continue  # Re-check this pet next iteration

            # PRIORITY 2: Heal if hurt and not mortaled
            if hp_pct < HEAL_THRESHOLD and not pet.IsYellowHits:
                # Heal loop until pet is above HEAL_UNTIL threshold
                while get_hp_percent(pet) < HEAL_UNTIL and not API.StopRequested:
                    # Re-fetch pet to get updated stats
                    pet = API.FindMobile(pet.Serial)
                    if not pet or pet.IsDead:
                        break

                    # Check for poison interruption
                    if pet.IsPoisoned:
                        break  # Exit heal loop, poison takes priority

                    # Check for mortal strike
                    if pet.IsYellowHits:
                        break  # Can't heal while mortaled

                    heal_pet(pet)

                continue  # Move to next pet

            # PRIORITY 3: Gift of Renewal (HoT) if HP deficit and not poisoned
            if hp_pct < RENEWAL_THRESHOLD and can_apply_renewal(pet):
                cast_gift_of_renewal(pet)

        # Pause between checks to reduce CPU usage
        API.Pause(CHECK_INTERVAL)

    API.SysMsg("Tamer Helper stopped", 32)


# =============================================================================
# SCRIPT ENTRY POINT
# =============================================================================

main_loop()
