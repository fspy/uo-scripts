"""Generic Skill Trainer for TazUO Legion Scripts.

Provides skill training with an in-game gump for selecting skills to train.
Supports both targeted and self-targeting skills.

Usage:
    Run this script directly to show the skill selection gump:
    python skills/trainer.py (or run from TazUO client)

    Or import individual skill functions:
    from skills.trainer import arms_lore, hiding
"""

import API
from _lib.utils import Hue, h, p

# Skill configurations
# Format: skill_name: {"targeted": bool, "pause": float}
SKILL_CONFIGS = {
    "Arms Lore": {"targeted": True, "pause": 0.85},
    "Item Identification": {"targeted": True, "pause": 0.85},
    "Taste Identification": {"targeted": True, "pause": 0.85},
    "Detecting Hidden": {"targeted": True, "pause": 10},
    "Begging": {"targeted": True, "pause": 1.0},
    "Hiding": {"targeted": False, "pause": 1.0},
    "Poisoning": {"targeted": True, "pause": 10.0},
    "Stealing": {"targeted": True, "pause": 9.0},
}


def train_skill(skill_name: str, target=None, pause=None):
    """
    Train a skill until capped.

    Args:
        skill_name: Name of skill to train (e.g., "Arms Lore")
        target: Target serial (if targeted skill). If None, prompts user.
        pause: Seconds to pause between attempts (uses config default if None)
    """
    config = SKILL_CONFIGS.get(skill_name, {"targeted": True, "pause": 0.85})
    if pause is None:
        pause = config["pause"]

    skill = API.GetSkill(skill_name)
    if not skill:
        p(f"Skill '{skill_name}' not found!", Hue.Red)
        return

    # Get target if needed
    if config["targeted"] and target is None:
        h(f"Select target for {skill_name}", API.Player, Hue.Orange)
        target = API.RequestTarget()
        if not target:
            p("No target selected", Hue.Red)
            return

    p(f"Training {skill_name} to {skill.Cap}...", Hue.Green)

    while skill.Value < skill.Cap and not API.StopRequested:
        API.UseSkill(skill_name)

        if config["targeted"]:
            if API.WaitForTarget(timeout=1.0):
                API.Target(target)  # pyright: ignore

        API.Pause(pause)

    p(f"{skill_name} complete!", Hue.Green)


def train_self_skill(skill_name: str, pause=1):
    """Train a self-targeting skill."""
    train_skill(skill_name, target=None, pause=pause)


# Convenience functions for common skills
def arms_lore(target=None):
    """Train Arms Lore on an item."""
    train_skill("Arms Lore", target)


def item_id(target=None):
    """Train Item Identification on an item."""
    train_skill("Item Identification", target)


def taste_id(target=None):
    """Train Taste Identification on a food item."""
    train_skill("Taste Identification", target)


def detecting_hidden(target=None):
    """Train Detecting Hidden on self."""
    train_skill("Detecting Hidden", target)


def begging(target=None):
    """Train Begging on an NPC."""
    train_skill("Begging", target)


def hiding():
    """Train Hiding skill."""
    train_skill("Hiding")


def poisoning(weapon=None):
    """
    Train Poisoning on a weapon.

    Args:
        weapon: Weapon serial. If None, prompts user to select.
    """
    if weapon is None:
        h("Select weapon to poison", API.Player, Hue.Orange)
        weapon = API.RequestTarget()
        if not weapon:
            p("No weapon selected", Hue.Red)
            return

    skill = API.GetSkill("Poisoning")
    p(f"Training Poisoning to {skill.Cap}...", Hue.Green)

    while skill.Value < skill.Cap and not API.StopRequested:
        if not API.FindType(0x0F0A, API.Backpack):
            p("Out of poison potions!", Hue.Red)
            break

        API.UseSkill("Poisoning")
        if API.WaitForTarget():
            API.Target(API.Found)  # pyright: ignore
        if API.WaitForTarget():
            API.Target(weapon)  # pyright: ignore

        API.Pause(10)


def steal(item_serial: int):
    """
    Train Stealing on a specific item.

    Args:
        item_serial: Serial of item to steal (e.g., from pack animal)
    """
    skill = API.GetSkill("Stealing")
    p(f"Training Stealing to {skill.Cap}...", Hue.Green)

    while skill.Value < skill.Cap and not API.StopRequested:
        API.UseSkill("Stealing")
        if API.WaitForTarget(timeout=0.5):
            API.Target(API.FindItem(item_serial))  # pyright:ignore
            API.Pause(1)

        if API.InJournal("successfully steal the item", True):
            API.Organizer("stealing")

        API.Pause(9)


def show_skill_gump():
    """Display gump for selecting skill to train."""
    # Shared state for callback
    selected_skill = [None]

    def make_callback(skill_name):
        def callback():
            selected_skill[0] = skill_name

        return callback

    # Create gump
    button_height = 30
    button_spacing = 5
    gump_width = 250
    num_skills = len(SKILL_CONFIGS)
    gump_height = 60 + (num_skills * (button_height + button_spacing))

    g = API.CreateGump()
    g.SetRect(100, 100, gump_width, gump_height)

    # Title
    title = API.CreateGumpLabel("Select Skill to Train", hue=53)
    title.SetPos(10, 10)
    g.Add(title)

    # Create button for each skill
    for i, skill_name in enumerate(SKILL_CONFIGS.keys()):
        btn = API.CreateSimpleButton(skill_name, gump_width - 20, button_height)
        btn.SetPos(10, 40 + (i * (button_height + button_spacing)))
        API.AddControlOnClick(btn, make_callback(skill_name))
        g.Add(btn)

    API.AddGump(g)
    p("Select a skill to train...", Hue.Cyan)

    # Wait for selection
    while not API.StopRequested:
        API.ProcessCallbacks()
        if selected_skill[0] is not None:
            skill_name = selected_skill[0]
            g.Dispose()
            return skill_name
        API.Pause(0.1)

    return None


def main():
    """Main entry point - shows skill selection gump."""
    skill_name = show_skill_gump()
    if skill_name:
        train_skill(skill_name)


main()
