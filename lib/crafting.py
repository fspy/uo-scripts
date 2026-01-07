"""Shared crafting utilities for ez* trainer scripts.

Provides helpers for gump-based crafting training including page navigation,
tool replacement, and skill bracket management.

Note: API module is injected by Legion engine at runtime as a global.
Import is wrapped in try/except for type hints in editors.
"""

# pyright: basic
# Try to import API for type hints, but don't fail if unavailable
try:
    import API
except (ImportError, NameError):
    pass  # API is injected at runtime by Legion engine

# Import move_item_robust and find_salvage_bag for salvage operations
from lib.items import move_item_robust, find_salvage_bag, drop_items_to_container
from lib.persistence import load_int, save_int

# Tool type constants
SCISSORS_TYPE = 0xF9F
TONGS_TYPE = 0x0FBB
HATCHET_TYPE = 0x0F43

# Crafting constants
CRAFTING_GUMP = 0x38920ABD
SALVAGE_ITEM_THRESHOLD = 100
SALVAGE_WEIGHT_THRESHOLD = API.Player.WeightMax - 20
SALVAGE_CONTEXT_MENU_INDEX = 2  # "Salvage All"

# Material weights (stones per unit)
MATERIAL_WEIGHTS = {
    0x1BF2: 0.1,  # Iron ingots
    0xF95: 0.1,  # Cloth
    0x1081: 1.0,  # Leather
    0x1BD7: 1.0,  # Boards
    0xEF3: 1.0,  # Blank scrolls
}
DEFAULT_MATERIAL_WEIGHT = 0.1  # Fallback for unknown types


class PageTracker:
    """
    Track current gump page to avoid redundant navigation.

    Crafting gumps have multiple pages. This tracker ensures we only send
    page navigation commands when actually changing pages, reducing server
    traffic and improving performance.

    Example:
        tracker = PageTracker()
        page = tracker.get_page(15)  # Returns 15 (first call)
        page = tracker.get_page(15)  # Returns None (already on page 15)
        page = tracker.get_page(22)  # Returns 22 (changed page)
    """

    def __init__(self):
        self._current_page = None

    def get_page(self, target_page):
        """
        Returns page number only on first call for that page, None after.

        Args:
            target_page: Page number to navigate to

        Returns:
            Page number if navigation needed, None if already on that page
        """
        if self._current_page != target_page:
            self._current_page = target_page
            return target_page
        return None

    def reset(self):
        """Reset page tracking (call when gump closes/reopens)."""
        self._current_page = None


def find_tool_strict(tool_type, container_serial):
    """
    Find a crafting tool ONLY in the specified container, no fallback.
    Opens the container first to ensure contents are loaded.

    Args:
        tool_type: Tool graphic ID (e.g., 0xF9D for sewing kit)
        container_serial: Container serial to search

    Returns:
        Tool item object, or None if not found
    """
    # Open container to ensure contents are loaded
    API.UseObject(container_serial)
    API.Pause(0.3)

    # Search only in specified container
    tool = API.FindType(tool_type, container_serial)
    return tool


def ensure_salvage_tool_outside(salvage_bag_serial, salvage_tool_type):
    """
    Ensure there's a salvage tool in backpack (outside the salvage bag).
    If all tools are inside the bag, move one outside.

    Args:
        salvage_bag_serial: The salvage bag serial
        salvage_tool_type: Tool graphic (scissors or tongs)

    Returns:
        True if tool is available outside, False if none available anywhere
    """
    # Check if there's already a tool outside the salvage bag (in backpack root)
    tools_in_backpack = API.FindTypeAll(salvage_tool_type, API.Player.Backpack) or []
    for tool in tools_in_backpack:
        # Make sure it's not inside the salvage bag
        if tool.Container != salvage_bag_serial:
            return True  # Found a tool outside

    # No tools outside, check inside salvage bag
    API.UseObject(salvage_bag_serial)
    API.Pause(0.3)

    tools_in_bag = API.FindTypeAll(salvage_tool_type, salvage_bag_serial) or []
    if not tools_in_bag:
        return False  # No tools anywhere

    # Move one tool from bag to backpack
    tool_to_move = tools_in_bag[0]
    if move_item_robust(tool_to_move.Serial, API.Player.Backpack, 1):
        API.SysMsg(f"Moved salvage tool outside bag", 68)
        return True

    return False


def validate_salvage_setup(salvage_bag_serial, crafting_tool_type, salvage_tool_type):
    """
    Validate and fix salvage bag setup for crafting.

    Checks/fixes:
    1. Crafting tools exist inside salvage bag
    2. Salvage tool exists outside (moves one out if needed)

    Args:
        salvage_bag_serial: The salvage bag serial
        crafting_tool_type: Tool used for crafting (sewing kit, tongs, etc.)
        salvage_tool_type: Tool needed outside for salvage (scissors, tongs)

    Returns:
        (success: bool, error_message: str or None)
    """
    # Open salvage bag
    API.UseObject(salvage_bag_serial)
    API.Pause(0.3)

    # Check for crafting tools inside salvage bag
    crafting_tools_inside = (
        API.FindTypeAll(crafting_tool_type, salvage_bag_serial) or []
    )
    if not crafting_tools_inside:
        return (False, "No crafting tools found inside salvage bag!")

    # Ensure salvage tool is outside
    if not ensure_salvage_tool_outside(salvage_bag_serial, salvage_tool_type):
        return (
            False,
            "No salvage tools found! Add scissors/tongs to backpack or salvage bag.",
        )

    return (True, None)


def get_target_skill(skill_name, target_override=None):
    """
    Get target skill level (uses cap if override is None).

    Args:
        skill_name: Name of the skill (e.g., 'Blacksmithy')
        target_override: Optional target skill value, None to use skill cap

    Returns:
        Target skill value (float)
    """
    if target_override is None:
        return API.GetSkill(skill_name).Cap
    return target_override


def should_continue_training(skill_name, target_skill):
    """
    Check if training should continue.

    Args:
        skill_name: Name of the skill being trained
        target_skill: Target skill value to reach

    Returns:
        True if should continue training, False if done or stop requested
    """
    return not API.StopRequested and API.GetSkill(skill_name).Value < target_skill


def salvage_if_needed(
    item_threshold=SALVAGE_ITEM_THRESHOLD, weight_threshold=SALVAGE_WEIGHT_THRESHOLD
):
    """
    Salvage crafted items when over threshold.

    Checks backpack item count and player weight. If either exceeds threshold,
    finds salvage bag and triggers salvage via context menu.

    Args:
        item_threshold: Max items in backpack before salvaging (default 100)
        weight_threshold: Max weight before salvaging (default 450)

    Returns:
        True if salvage not needed or succeeded, False if salvage needed but failed
    """
    over_items = API.Contents(API.Backpack) > item_threshold
    over_weight = API.Player.Weight > weight_threshold

    if over_items or over_weight:
        salvage_bag = find_salvage_bag()
        if salvage_bag:
            API.ContextMenu(salvage_bag, SALVAGE_CONTEXT_MENU_INDEX)
            API.Pause(0.65)
            return True
        else:
            API.SysMsg("No salvage bag found!", 32)
            return False
    return True


def destroy_items_with_axe(item_types, item_threshold=None, weight_threshold=None):
    """
    Destroy crafted items using a hatchet.

    For carpentry and other crafts where salvage doesn't work. Uses a hatchet
    to destroy items (no materials returned).

    DEPRECATED: Use trash_items() instead - many items can't be axe-destroyed.

    Args:
        item_types: List of item graphic IDs to destroy
        item_threshold: Only destroy if backpack has more than this many items (None = always destroy)
        weight_threshold: Only destroy if weight exceeds this (None = always destroy)

    Returns:
        True if destruction not needed or succeeded, False if failed
    """
    # Check thresholds if specified
    if item_threshold is not None or weight_threshold is not None:
        if weight_threshold is None:
            weight_threshold = API.Player.WeightMax - 20

        item_count = API.Contents(API.Backpack)
        weight = API.Player.Weight

        over_items = item_threshold is None or item_count > item_threshold
        over_weight = weight_threshold is None or weight > weight_threshold

        if not (over_items or over_weight):
            return True  # No destruction needed

    # Find hatchet in backpack
    hatchet = API.FindType(HATCHET_TYPE, API.Player.Backpack)
    if not hatchet:
        API.SysMsg("No hatchet found for destroying items!", 32)
        return False

    destroyed_count = 0

    # Destroy all items of specified types
    for item_type in item_types:
        items = API.FindTypeAll(item_type, API.Player.Backpack) or []
        for item in items:
            API.UseObject(hatchet.Serial)
            if API.WaitForTarget("any", 0.5):
                API.Target(item.Serial)  # type: ignore
                API.Pause(0.3)
                destroyed_count += 1

    if destroyed_count > 0:
        API.SysMsg(f"Destroyed {destroyed_count} items", 68)

    return True


def trash_items(
    trash_container,
    item_types,
    source_container=None,
    item_threshold=SALVAGE_ITEM_THRESHOLD,
    weight_threshold=None,
):
    """
    Trash crafted items by dropping them into a trash container.

    For carpentry and other crafts where salvage doesn't work. Drops all
    items of specified types into a trash barrel or container.

    Uses thresholds to batch trash operations (similar to salvage).

    Args:
        trash_container: Trash container serial to drop items into
        item_types: List of item graphic IDs to trash
        source_container: Source container to pull items from (defaults to backpack)
        item_threshold: Only trash when backpack has more than this many items (default 100)
        weight_threshold: Only trash when weight exceeds this (default: WeightMax - 20)

    Returns:
        True if trash not needed or succeeded, False if failed (no container)
    """
    if not trash_container:
        API.SysMsg("No trash container configured!", 32)
        return False

    # Check thresholds first (batch trash operations for performance)
    if weight_threshold is None:
        weight_threshold = API.Player.WeightMax - 20

    over_items = API.Contents(API.Backpack) > item_threshold
    over_weight = API.Player.Weight > weight_threshold

    if not (over_items or over_weight):
        return True  # No trash needed yet

    # Container already opened at startup, no need to re-open
    # Drop all items of specified types from source
    trashed = drop_items_to_container(
        trash_container, item_types, source=source_container
    )

    if trashed > 0:
        API.SysMsg(f"Trashed {trashed} item stack(s)", 68)

    return True


def count_materials(material_types):
    """
    Count total materials in backpack.

    Args:
        material_types: List of material graphic IDs to count

    Returns:
        Total count of all material types
    """
    total = 0
    for mat_type in material_types:
        items = API.FindTypeAll(mat_type, API.Player.Backpack) or []
        for item in items:
            total += getattr(item, "Amount", 0) or 0
    return total


def get_material_weight(graphic):
    """
    Get weight per unit for a material type.

    Args:
        graphic: Material graphic ID

    Returns:
        Weight in stones per unit
    """
    return MATERIAL_WEIGHTS.get(graphic, DEFAULT_MATERIAL_WEIGHT)


def grab_materials_by_weight(container_serial, material_types, weight_buffer=20):
    """
    Pull materials from container until weight limit reached.

    Moves materials to backpack, respecting different material weights.
    Stops when player is within weight_buffer stones of max weight.

    Only grabs items with hue 0 (default color) to avoid taking colored
    ore ingots, special cloths, or other valuable dyed materials.

    Note: Container should be pre-opened at startup for performance.

    Args:
        container_serial: Storage container serial
        material_types: List of material graphic IDs to grab
        weight_buffer: Stones to leave free (don't fill completely)

    Returns:
        Number of material units moved
    """
    # Container already opened at startup, no need to re-open
    moved_count = 0
    available_weight = API.Player.WeightMax - API.Player.Weight - weight_buffer

    for mat_type in material_types:
        if available_weight <= 0:
            break

        mat_weight = get_material_weight(mat_type)
        items = API.FindTypeAll(mat_type, container_serial) or []

        for item in items:
            if available_weight <= 0:
                break

            # Only grab hue 0 (default color) items to avoid colored materials
            item_hue = getattr(item, "Hue", -1)
            if item_hue != 0:
                continue  # Skip colored/dyed materials

            amount = getattr(item, "Amount", 0) or 0
            can_grab = min(amount, int(available_weight / mat_weight))

            if can_grab > 0:
                if move_item_robust(item.Serial, API.Player.Backpack, can_grab):
                    moved_count += can_grab
                    available_weight -= can_grab * mat_weight

    return moved_count


def restock_if_needed(config, storage_serial):
    """
    Check materials and restock if low.

    Flow:
    1. Check if materials below threshold
    2. If low: force salvage to recover materials
    3. If still low: grab from storage container (fills by weight)
    4. If still low after grab: storage is empty, return False

    Uses hysteresis: triggers restock at threshold (default 50), but fills
    by available weight (typically 150-200+ materials), preventing frequent
    restock checks.

    Args:
        config: Craft trainer config dict with material_types and material_threshold
        storage_serial: Storage container serial to pull from

    Returns:
        True if we have enough materials to continue, False if storage empty
    """
    material_types = config.get("material_types")
    if not material_types:
        return True  # No restock configured

    threshold = config.get("material_threshold", 50)
    salvage_tool_type = config.get("salvage_tool_type")

    # Check if we need to restock
    current = count_materials(material_types)
    if current >= threshold:
        return True  # Have enough materials

    # Low on materials - salvage first to recover
    API.SysMsg(f"Low materials ({current}) - salvaging & restocking...", 68)

    if salvage_tool_type:
        salvage_if_needed(item_threshold=0, weight_threshold=0)  # Force salvage
        API.Pause(1.0)
        current = count_materials(material_types)

    # Check again after salvage
    if current >= threshold:
        API.SysMsg(f"Salvage recovered enough - continuing ({current} materials)", 68)
        return True  # Salvage gave us enough

    # Still low - pull from storage (fills by weight)
    if not storage_serial:
        API.SysMsg("No storage container configured - stopping", 32)
        return False

    grabbed = grab_materials_by_weight(storage_serial, material_types)

    if grabbed == 0:
        API.SysMsg("Storage empty - stopping", 32)
        return False

    after = count_materials(material_types)
    API.SysMsg(f"Restocked: {current} -> {after} materials", 68)
    return True


def cleanup_craft_trainer(config, storage_serial):
    """
    Clean up after crafting session ends.

    Salvages remaining crafted items and returns raw materials to storage.

    Args:
        config: Craft trainer config dict with salvage_tool_type and material_types
        storage_serial: Storage container serial to return materials to
    """
    salvage_tool_type = config.get("salvage_tool_type")
    material_types = config.get("material_types")

    if not storage_serial or not material_types:
        return  # Nothing to clean up

    API.SysMsg("Cleaning up - salvaging remaining items...", 68)

    # Force salvage everything in backpack
    if salvage_tool_type:
        salvage_if_needed(item_threshold=0, weight_threshold=0)
        API.Pause(1.0)

    # Count materials before returning
    before = count_materials(material_types)
    if before == 0:
        API.SysMsg("No materials to return", 68)
        return

    # Return materials to storage
    API.SysMsg(f"Returning {before} materials to storage...", 68)
    API.UseObject(storage_serial)  # Open container
    API.Pause(0.5)

    dropped = drop_items_to_container(storage_serial, material_types)

    if dropped > 0:
        API.SysMsg(f"Returned {dropped} stack(s) to storage", 68)


def run_craft_trainer(config):
    """
    Generic craft training loop.

    Trains a crafting skill using a configuration dict. Handles tool management,
    salvage bag setup, skill brackets, and the main crafting loop.

    Args:
        config: Configuration dict with keys:
            - skill_name (str): Name of skill (e.g., 'Blacksmithy')
            - tool_type (int): Tool graphic ID (e.g., 0x0FBB for tongs)
            - salvage_tool_type (int or None): Tool for salvage, None to skip salvage
            - brackets (list): List of bracket dicts with max_skill, page, button, desc
            - target_skill (float or None): Target skill value, None for skill cap
            - material_types (list, optional): Material graphic IDs for restocking
            - material_threshold (int, optional): Restock when materials below this
            - storage_key (str, optional): Persistence key for storage container

    Example config:
        {
            'skill_name': 'Blacksmithy',
            'tool_type': 0x0FBB,
            'salvage_tool_type': TONGS_TYPE,
            'target_skill': 90.0,
            'brackets': [
                {'max_skill': 45.0, 'page': 43, 'button': 9, 'desc': 'mace'},
                # ... more brackets
            ],
            'material_types': [0x1BF2],  # Iron ingots
            'material_threshold': 50,
            'storage_key': 'ezSmith.Storage',
        }
    """
    skill_name = config["skill_name"]
    tool_type = config["tool_type"]
    salvage_tool_type = config.get("salvage_tool_type")
    brackets = config["brackets"]
    target_skill = config.get("target_skill")

    # Setup storage container for restocking (if configured)
    storage_serial = None
    if config.get("material_types") and config.get("storage_key"):
        storage_key = config["storage_key"]
        storage_serial = load_int(storage_key, 0)
        if not storage_serial:
            API.SysMsg("Target your material storage container", 68)
            storage_serial = API.RequestTarget()
            if storage_serial:
                save_int(storage_key, storage_serial)
                API.SysMsg("Storage container saved", 68)
            else:
                API.SysMsg(
                    "No storage container targeted - continuing without restock", 33
                )

    # Setup trash container for disposing items (if configured)
    trash_serial = None
    if config.get("trash_item_types") and config.get("trash_container_key"):
        trash_key = config["trash_container_key"]
        trash_serial = load_int(trash_key, 0)
        if not trash_serial:
            API.SysMsg("Target your trash container", 68)
            trash_serial = API.RequestTarget()
            if trash_serial:
                save_int(trash_key, trash_serial)
                API.SysMsg("Trash container saved", 68)
            else:
                API.SysMsg("No trash container targeted - items may accumulate", 33)

    # Setup based on whether salvage is used
    if salvage_tool_type:
        # Salvage-enabled crafting (smith, tailor)
        salvage_bag = find_salvage_bag()
        if not salvage_bag:
            API.SysMsg("No salvage bag found in backpack!", 32)
            API.Stop()
            return

        tool_container = salvage_bag
        success, error = validate_salvage_setup(
            salvage_bag, tool_type, salvage_tool_type
        )
        if not success:
            API.SysMsg(error or "Salvage setup validation failed", 32)
            API.Stop()
            return
        strict = True
    else:
        # No salvage (tinkering, carpentry, etc.) - use salvage bag for organization if available
        tool_container = find_salvage_bag() or API.Player.Backpack
        strict = False

    # Pre-open storage and trash containers so contents are loaded (performance optimization)
    if storage_serial:
        API.UseObject(storage_serial)
        API.Pause(0.3)
    if trash_serial:
        API.UseObject(trash_serial)
        API.Pause(0.3)

    # Open crafting gump
    if not open_craft_gump(tool_type, tool_container, CRAFTING_GUMP, strict=strict):
        API.SysMsg("Failed to open crafting gump!", 32)
        API.Stop()
        return

    target = get_target_skill(skill_name, target_skill)
    API.SysMsg(f"Training {skill_name} to {target}", 68)

    page_tracker = PageTracker()

    # Main training loop
    while should_continue_training(skill_name, target):
        skill = API.GetSkill(skill_name).Value
        bracket = get_craft_bracket(skill, brackets)

        if not bracket:
            API.Stop()
            break

        page, button = bracket

        # Start the craft (gump closes, craft begins in background)
        start_craft(CRAFTING_GUMP, page_tracker.get_page(page), button)

        # Do work WHILE craft is happening (true parallelism!)
        if salvage_tool_type:
            if not salvage_if_needed():
                API.Stop()
                break
        elif config.get("trash_item_types") and trash_serial:
            # Use trash container for non-salvageable items (carpentry, etc.)
            # Items are in tool_container (salvage bag or backpack)
            if not trash_items(
                trash_serial,
                config["trash_item_types"],
                source_container=tool_container,
            ):
                API.Stop()
                break

        # Restock if needed (also while craft is happening)
        if config.get("material_types"):
            if not restock_if_needed(config, storage_serial):
                API.Stop()
                break

        # Now wait for craft to complete
        wait_for_gump_or_replace_tool(
            CRAFTING_GUMP, tool_type, tool_container, strict=strict
        )

    # Training complete
    final_skill = API.GetSkill(skill_name).Value
    API.SysMsg(f"Training complete! {skill_name}: {final_skill:.1f}", 68)

    # Cleanup: salvage and return materials
    if config.get("material_types") and storage_serial:
        cleanup_craft_trainer(config, storage_serial)


def get_craft_bracket(skill_value, brackets):
    """
    Find the appropriate craft bracket for current skill level.

    Brackets define what item to craft at each skill range. Each bracket
    is a dict specifying the maximum skill for that item and the gump page/button.

    Args:
        skill_value: Current skill value (e.g., 45.5)
        brackets: List of bracket dicts with keys: max_skill, page, button, desc
                  Example: [
                      {'max_skill': 40.0, 'page': None, 'button': None, 'desc': 'too low'},
                      {'max_skill': 50.0, 'page': 15, 'button': 2, 'desc': 'scissors'}
                  ]

    Returns:
        (page, button) tuple if valid bracket found
        None if skill too low (page=None in bracket) or above all brackets

    Example:
        bracket = get_craft_bracket(45.0, SKILL_BRACKETS)
        if bracket:
            page, button = bracket
            craft_item(GUMP_ID, page, button)
        else:
            API.Stop()  # Skill too low or training complete
    """
    for bracket in brackets:
        if skill_value < bracket["max_skill"]:
            if bracket["page"] is None:
                # Special bracket indicating skill too low for automated training
                API.SysMsg(f"Skill too low: {bracket['desc']}", 32)
                return None
            return (bracket["page"], bracket["button"])

    # Skill above all brackets - training complete
    return None


def find_tool(tool_type, tool_container):
    """
    Find a crafting tool in container with fallback to backpack.

    NOTE: For salvage bag workflows, use find_tool_strict() instead to ensure
    tools come from inside the salvage bag (so crafted items go inside).

    Searches tool_container first, then falls back to player's backpack
    if not found. This allows flexible tool storage.

    Args:
        tool_type: Tool graphic ID (e.g., 0xF9D for sewing kit)
        tool_container: Container serial to search first

    Returns:
        Tool item object, or None if not found
    """
    # Try configured container first
    tool = API.FindType(tool_type, tool_container)
    if tool:
        return tool

    # Fallback to backpack
    if tool_container != API.Player.Backpack:
        tool = API.FindType(tool_type, API.Player.Backpack)
        if tool:
            return tool

    return None


def open_craft_gump(tool_type, tool_container, gump_id, timeout=2.0, strict=False):
    """
    Open crafting gump by using a tool.

    IMPORTANT: Call this at script startup to prevent forced disconnect
    when trying to interact with a gump that doesn't exist.

    Args:
        tool_type: Tool graphic ID
        tool_container: Container serial to search for tools
        gump_id: Expected gump ID
        timeout: Seconds to wait for gump to appear
        strict: If True, use find_tool_strict (no backpack fallback)

    Returns:
        True if gump opened successfully, False otherwise
    """
    if strict:
        tool = find_tool_strict(tool_type, tool_container)
    else:
        tool = find_tool(tool_type, tool_container)

    if not tool:
        API.SysMsg("No tools found!", 32)
        return False

    API.UseObject(tool.Serial)
    return API.WaitForGump(gump_id, timeout)


def wait_for_gump_or_replace_tool(gump_id, tool_type, tool_container, strict=False):
    """
    Wait for crafting gump to reappear, replacing worn tools automatically.

    After crafting an item, the gump closes briefly then reopens. If the tool
    breaks during crafting, this function detects the journal message and
    automatically uses a new tool from storage.

    Args:
        gump_id: Crafting gump ID to wait for
        tool_type: Tool graphic ID (for replacement)
        tool_container: Container serial to search for tools
        strict: If True, use find_tool_strict (no backpack fallback)

    Returns:
        None (stops script if no tools available)
    """
    while not API.HasGump(gump_id):
        # Check if tool broke
        if API.InJournal("worn out your tool", True):
            if strict:
                tool = find_tool_strict(tool_type, tool_container)
            else:
                tool = find_tool(tool_type, tool_container)

            if not tool:
                API.SysMsg("No tools left!", 32)
                API.Stop()
                return
            API.UseObject(tool.Serial)
            API.Pause(0.55)
        API.Pause(0.1)


def start_craft(gump_id, page, button):
    """
    Start crafting an item via gump - does NOT wait for completion.

    If page is provided, navigates to that page first. Then clicks the
    craft button and returns immediately. Craft happens in background.

    Use this to do work (trash/restock) while craft is in progress, then
    call wait_for_gump_or_replace_tool() to wait for completion.

    Args:
        gump_id: Crafting gump ID
        page: Page number to navigate to (None to skip navigation)
        button: Button ID to click for crafting
    """
    if page:
        API.ReplyGump(page, gump_id)
        API.WaitForGump(gump_id)

    API.ReplyGump(button, gump_id)
    # Craft is now in progress - gump will return when done


def craft_item(gump_id, page, button):
    """
    Craft an item via gump with page navigation.

    If page is provided, navigates to that page first. Then clicks the
    craft button and waits for confirmation.

    DEPRECATED: Use start_craft() + wait_for_gump_or_replace_tool() instead
    for better performance (allows parallel work during craft).

    Args:
        gump_id: Crafting gump ID
        page: Page number to navigate to (None to skip navigation)
        button: Button ID to click for crafting
    """
    if page:
        API.ReplyGump(page, gump_id)
        API.WaitForGump(gump_id)

    API.ReplyGump(button, gump_id)
    API.WaitForGump(gump_id)
