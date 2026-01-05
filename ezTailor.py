# ezTailor - Automated Tailoring Skill Training
# Copy this script to make ezBlacksmith, ezCarpentry, etc.

import API

# === CONFIGURATION ===
SKILL_NAME = "Tailoring"
TARGET_SKILL = 96.0  # Stop here. Set to None to train to skill cap.
CRAFTING_GUMP = 0x38920ABD
TOOL_TYPE = 0xF9D  # sewing kit
TOOL_CONTAINER = 0x4101CA29  # tools stored here, also salvage container
SALVAGE_ITEM_THRESHOLD = 100  # salvage when backpack has this many items
SALVAGE_WEIGHT_BUFFER = 50  # salvage when within this many stones of max weight

# Skill brackets: (max_skill, page, button, description)
SKILL_BRACKETS = [
    (29.0, None, None, "too low - train manually to 29.0 first"),
    (41.4, 15, 135, "short pants"),
    (50.0, 15, 51, "cloak"),
    (74.6, 29, 9, "fur boots"),
    (120.0, 22, 86, "oil cloth"),
]

# === SCRIPT STATE ===
_current_page = None


# === HELPER FUNCTIONS ===
def get_page(target_page):
    """Returns page number only on first call for that page, None after."""
    global _current_page
    if _current_page != target_page:
        _current_page = target_page
        return target_page
    return None


def salvage_if_needed():
    """Salvage crafted items if over item count or weight threshold."""
    over_items = API.Contents(API.Backpack) > SALVAGE_ITEM_THRESHOLD
    over_weight = (
        API.Player.Weight > 450
    )  # API.Player.WeightMax - SALVAGE_WEIGHT_BUFFER
    if over_items or over_weight:
        API.ContextMenu(TOOL_CONTAINER, 1)
        API.Pause(0.65)


def craft(gump, page, button):
    """Craft an item via gump."""
    if page:
        API.ReplyGump(page, gump)
        API.WaitForGump(gump)
    API.ReplyGump(button, gump)
    API.WaitForGump(gump)


def wait_for_gump():
    """Wait for crafting gump to reappear, replacing tools if worn out."""
    while not API.HasGump(CRAFTING_GUMP):
        if API.InJournal("worn out your tool", True):
            tool = API.FindType(TOOL_TYPE, TOOL_CONTAINER)
            if not tool:
                API.SysMsg("No tools left!", 32)
                API.Stop()
                return
            API.UseObject(tool.Serial)
            API.Pause(0.55)
        API.Pause(0.1)


def get_bracket(skill):
    """Return (page, button) for current skill level, or None to stop."""
    for max_skill, page, button, desc in SKILL_BRACKETS:
        if skill < max_skill:
            if page is None:
                API.SysMsg(f"Skill too low: {desc}", 32)
                return None
            return (page, button)
    return None


def get_target():
    """Return target skill - either TARGET_SKILL or the character's skill cap."""
    if TARGET_SKILL is None:
        return API.GetSkill(SKILL_NAME).Cap
    return TARGET_SKILL


def should_continue():
    """Check if training should continue."""
    return not API.StopRequested and API.GetSkill(SKILL_NAME).Value < get_target()


# === MAIN LOOP ===
def main():
    target = get_target()
    API.SysMsg(f"Training {SKILL_NAME} to {target}", 68)

    while should_continue():
        skill = API.GetSkill(SKILL_NAME).Value
        bracket = get_bracket(skill)

        if not bracket:
            API.Stop()
            break

        page, button = bracket
        craft(CRAFTING_GUMP, get_page(page), button)
        wait_for_gump()
        salvage_if_needed()

    # Training complete
    final_skill = API.GetSkill(SKILL_NAME).Value
    API.SysMsg(f"Training complete! {SKILL_NAME}: {final_skill:.1f}", 68)


main()
