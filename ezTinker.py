# ezTinker - Automated Tinkering Skill Training

import API
from lib.crafting import (
    PageTracker,
    get_craft_bracket,
    open_craft_gump,
    wait_for_gump_or_replace_tool,
    craft_item
)
from lib.items import find_salvage_bag

# === CONFIGURATION ===
SKILL_NAME = "Tinkering"
TARGET_SKILL = 70.1  # Stop here. Set to None to train to skill cap.
CRAFTING_GUMP = 0x38920ABD
TOOL_TYPE = 0x1EB8  # tinker tools
USES_SALVAGE_BAG = False  # Tinkering doesn't use salvage (can't salvage tinker items)
SALVAGE_ITEM_THRESHOLD = 100  # salvage when backpack has this many items
SALVAGE_WEIGHT_BUFFER = 50  # salvage when within this many stones of max weight

# Skill brackets: (max_skill, page, button, description)
SKILL_BRACKETS = [
    (40.0, None, None, "too low - train to 40 in new haven"),
    (45.0, 15, 2, "scissors"),
    (60.0, 15, 86, "tongs"),
    (75.0, 15, 121, "lockpick"),
    (85.0, 1, 9, "bracelet"),
    (90.0, 36, 37, "spyglass"),
    (100.0, 1, 2, "ring"),
]

# === SCRIPT STATE ===
page_tracker = PageTracker()


# === HELPER FUNCTIONS ===


def salvage_if_needed():
    """Salvage crafted items if over item count or weight threshold."""
    over_items = API.Contents(API.Backpack) > SALVAGE_ITEM_THRESHOLD
    over_weight = (
        API.Player.Weight > 450
    )  # API.Player.WeightMax - SALVAGE_WEIGHT_BUFFER
    if over_items or over_weight:
        # Find salvage bag dynamically
        salvage_bag = find_salvage_bag()
        if salvage_bag:
            API.ContextMenu(salvage_bag, 1)
            API.Pause(0.65)
        else:
            API.SysMsg("No salvage bag found! Please add a salvage bag to your backpack.", 32)
            API.Stop()





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
    # Use salvage bag for tool organization if available, otherwise use backpack
    tool_container = find_salvage_bag() or API.Player.Backpack
    
    # Open gump at startup to prevent DC from responding to non-existent gump
    if not open_craft_gump(TOOL_TYPE, tool_container, CRAFTING_GUMP):
        API.SysMsg("Failed to open crafting gump!", 32)
        API.Stop()
        return

    target = get_target()
    API.SysMsg(f"Training {SKILL_NAME} to {target}", 68)

    while should_continue():
        skill = API.GetSkill(SKILL_NAME).Value
        bracket = get_craft_bracket(skill, SKILL_BRACKETS)

        if not bracket:
            API.Stop()
            break

        page, button = bracket
        craft_item(CRAFTING_GUMP, page_tracker.get_page(page), button)
        wait_for_gump_or_replace_tool(CRAFTING_GUMP, TOOL_TYPE, tool_container)
        if SKILL_NAME in ["Blacksmithing", "Tailoring"]:
            salvage_if_needed()

    # Training complete
    final_skill = API.GetSkill(SKILL_NAME).Value
    API.SysMsg(f"Training complete! {SKILL_NAME}: {final_skill:.1f}", 68)


main()