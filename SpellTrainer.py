"""
Generic Spell Trainer Script
Trains spell-based skills from 0 to 100

Supports: Spellweaving, Magery, Necromancy

USAGE: Just change SKILL_NAME below to switch between skills.
"""

import API
import time
from enum import Enum
from lib.spells import calculate_recovery_time, calculate_full_spell_delay


# =============================================================================
# CONFIGURATION - Just change SKILL_NAME to switch presets
# =============================================================================

SKILL_NAME = "Chivalry"  # Options: "Spellweaving", "Magery", "Necromancy", "Chivalry"

# Healing config (set HEAL_SPELL to None to disable)
HEAL_SPELL = (
    "Greater Heal",
    2.0,
    11,
    True,
)  # (name, cast_time, mana_cost, target_self)
HEAL_THRESHOLD = 0.5

# Timing settings
BASE_RECOVERY = 1.5
MEDITATION_COOLDOWN = 10.0  # Meditation skill internal cooldown (seconds)
FCR_CAP = 6

# Other
FOLLOWER_DISMISS_DISTANCE = 2


# =============================================================================
# PRESETS - Auto-selected based on SKILL_NAME above
# =============================================================================

PRESETS = {
    "Spellweaving": {
        "fc_cap": 4,
        "phases": [
            (20, "Arcane Circle", 0.5, 24, False, "NONE"),
            (33, "Immolating Weapon", 1.0, 32, False, "NONE"),
            (44, "Reaper Form", 2.5, 34, False, "NONE"),
            (60, "Summon Fey", 1.5, 10, False, "DISMISS_FOLLOWERS"),
            (74, "Essence of Wind", 3.0, 40, False, "NONE"),
            (90, "Wildfire", 2.5, 50, True, "NONE"),
            (100, "Word of Death", 3.5, 50, True, "HEAL_CHECK"),
        ],
    },
    "Magery": {
        "fc_cap": 2,
        "phases": [
            (45, "Bless", 1.0, 9, True, "NONE"),
            (55, "Greater Heal", 1.25, 11, True, "NONE"),
            (65, "Magic Reflection", 1.75, 14, False, "NONE"),
            (75, "Invisibility", 1.75, 20, True, "NONE"),
            (90, "Mana Vampire", 2.0, 40, True, "NONE"),
            (100, "Earthquake", 2.25, 50, False, "NONE"),
        ],
    },
    "Necromancy": {
        "fc_cap": 2,
        "phases": [
            (50, "Pain Spike", 1.25, 5, True, "HEAL_CHECK"),
            (70, "Horrific Beast", 2.25, 11, False, "NONE"),
            (90, "Wither", 1.5, 23, False, "NONE"),
            (100, "Lich Form", 2.0, 23, False, "NONE"),
        ],
    },
    "Chivalry": {
        "fc_cap": 4,
        "phases": [
            (45, "Consecrate Weapon", 0.5, 10, False, "NONE"),
            (60, "Divine Fury", 1.5, 15, False, "NONE"),
            (70, "Enemy of One", 2, 20, False, "NONE"),
            (90, "Holy Light", 2, 10, False, "NONE"),
            (120, "Noble Sacrifice", 3, 20, False, "NONE"),
        ],
    },
}

# Auto-select preset
_preset = PRESETS[SKILL_NAME]
FC_CAP = _preset["fc_cap"]
TRAINING_PHASES = _preset["phases"]


# =============================================================================
# CORE FUNCTIONS - Do not edit below unless you know what you're doing
# =============================================================================

# Global state
last_meditation_time = 0


class Handler(Enum):
    NONE = None
    DISMISS_FOLLOWERS = "dismiss_followers"
    HEAL_CHECK = "heal_check"


def get_skill():
    """Get current skill value"""
    skill = API.GetSkill(SKILL_NAME)
    return skill.Value if skill else 0.0





def wait_for_mana(min_mana):
    """Wait until player has full mana, using meditation if needed"""
    global last_meditation_time

    if API.Player.Mana < min_mana:
        # Wait for meditation cooldown if needed
        current_time = time.time()
        time_since_last = current_time - last_meditation_time
        if time_since_last < MEDITATION_COOLDOWN:
            wait_time = MEDITATION_COOLDOWN - time_since_last
            API.Pause(wait_time)

        # Wait a bit before meditating so it isn't instantly cancelled
        API.Pause(0.5)
        API.UseSkill("Meditation")
        last_meditation_time = time.time()

        while API.Player.Mana < API.Player.ManaMax:
            if API.StopRequested:
                return False
            API.Pause(0.1)
    return True


def cast_spell(spell_name, base_cast_time, mana_cost, target_self=False):
    """Cast a spell and handle targeting if needed"""
    if not wait_for_mana(mana_cost):
        return False

    API.CastSpell(spell_name)

    if target_self:
        # Wait for target cursor (cast time consumed here)
        if API.WaitForTarget("any", 5):
            API.TargetSelf()
            # Only wait for recovery after targeting
            recovery = calculate_recovery_time(base_recovery=BASE_RECOVERY, fcr_cap=FCR_CAP)
            API.Pause(recovery)
    else:
        # Non-targeted spell - need full delay (cast + recovery)
        delay = calculate_full_spell_delay(
            base_cast_time, 
            fc_cap=FC_CAP, 
            base_recovery=BASE_RECOVERY, 
            fcr_cap=FCR_CAP
        )
        API.Pause(delay)

    return True


def dismiss_followers():
    """Dismiss followers when at max capacity"""
    if API.Player.Followers >= API.Player.FollowersMax:
        followers = API.GetAllMobiles(distance=FOLLOWER_DISMISS_DISTANCE)
        for follower in followers:
            # Use context menu #5 for dismiss
            API.ContextMenu(follower.Serial, 5)
            API.Pause(0.5)
            if API.Player.Followers < API.Player.FollowersMax:
                break


def heal_if_needed():
    """Check health and heal if needed"""
    if HEAL_SPELL is None:
        return

    if API.Player.Hits < API.Player.HitsMax * HEAL_THRESHOLD:
        spell_name, base_cast_time, mana_cost, target_self = HEAL_SPELL
        cast_spell(spell_name, base_cast_time, mana_cost, target_self)


def train_phase(end_skill, spell_name, base_cast_time, mana_cost, target_self, handler):
    """Train a specific skill range with optional special handling"""
    skill = get_skill()
    skill_cap = API.GetSkill(SKILL_NAME).Cap

    while skill < end_skill and skill < skill_cap and not API.StopRequested:
        if handler == "DISMISS_FOLLOWERS":
            dismiss_followers()
        elif handler == "HEAL_CHECK":
            heal_if_needed()

        cast_spell(spell_name, base_cast_time, mana_cost, target_self)
        skill = get_skill()


def main():
    skill_cap = API.GetSkill(SKILL_NAME).Cap
    
    for phase in TRAINING_PHASES:
        if API.StopRequested:
            break

        end_skill, spell_name, base_cast_time, mana_cost, target_self, handler = phase
        current_skill = get_skill()

        # Stop if we've reached skill cap
        if current_skill >= skill_cap:
            API.SysMsg(f"{SKILL_NAME} at cap ({skill_cap})", 68)
            break

        if current_skill < end_skill:
            train_phase(
                end_skill, spell_name, base_cast_time, mana_cost, target_self, handler
            )


while not API.StopRequested:
    main()

