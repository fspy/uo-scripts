# ezSmith - Automated Blacksmithing Skill Training

import API
from lib.crafting import (
    PageTracker,
    get_craft_bracket,
    open_craft_gump,
    wait_for_gump_or_replace_tool,
    craft_item,
    validate_salvage_setup,
    TONGS_TYPE,
)
from lib.items import find_salvage_bag

# === CONFIGURATION ===
SKILL_NAME = "Blacksmithy"
TARGET_SKILL = 90.0  # Stop here. Set to None to train to skill cap.
CRAFTING_GUMP = 0x38920ABD
TOOL_TYPE = 0x0FBB  # tongs
USES_SALVAGE_BAG = True  # Blacksmithing uses salvage bags
SALVAGE_TOOL_TYPE = TONGS_TYPE  # tongs are both craft and salvage tool
SALVAGE_ITEM_THRESHOLD = 100  # salvage when backpack has this many items
SALVAGE_WEIGHT_BUFFER = 50  # salvage when within this many stones of max weight

# Skill brackets: (max_skill, page, button, description)
SKILL_BRACKETS = [
    (40.0, None, None, "too low - train to 40 in new haven"),
    (45.0, 43, 9, "mace"),
    (50.0, 43, 16, "maul"),
    (55.0, 22, 23, "cutlass"),
    (59.5, 22, 37, "katana"),
    (70.5, 22, 58, "scimitar"),
    (106.4, 1, 65, "platemail gorget"),
    (108.9, 1, 58, "platemail gloves"),
    (116.3, 1, 51, "platemail arms"),
    (118.8, 1, 72, "platemail legs"),
    (120.0, 1, 79, "platemail tunics"),
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
            API.ContextMenu(salvage_bag, 2)
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
    # Find and validate salvage bag setup
    salvage_bag = find_salvage_bag()
    if not salvage_bag:
        API.SysMsg("No salvage bag found in backpack!", 32)
        API.Stop()
        return
    
    tool_container = salvage_bag
    
    # Validate salvage setup (tools inside, salvage tool outside)
    success, error = validate_salvage_setup(salvage_bag, TOOL_TYPE, SALVAGE_TOOL_TYPE)
    if not success:
        API.SysMsg(error or "Salvage setup validation failed", 32)
        API.Stop()
        return
    
    # Open gump at startup to prevent DC from responding to non-existent gump
    if not open_craft_gump(TOOL_TYPE, tool_container, CRAFTING_GUMP, strict=True):
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
        wait_for_gump_or_replace_tool(CRAFTING_GUMP, TOOL_TYPE, tool_container, strict=True)
        salvage_if_needed()

    # Training complete
    final_skill = API.GetSkill(SKILL_NAME).Value
    API.SysMsg(f"Training complete! {SKILL_NAME}: {final_skill:.1f}", 68)


main()
