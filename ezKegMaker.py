# ezKegMaker.py - Batch craft potion kegs from raw materials
#
# Workflow (makes one complete keg at a time):
#   1. Check materials (7 ingots, 23 boards, 10 bottles)
#   2. Tinkering: check/craft tools, barrel tap, barrel hoops
#   3. Carpentry: 3x staves, 2x lids, keg
#   4. Tinkering: potion keg (assembly)
#   5. Move finished keg to storage
#   6. Repeat for BATCH_SIZE
#
# Features:
#   - One-keg-at-a-time crafting (better weight management)
#   - Auto tool crafting (maintains 2+ tinker tools and saws)
#   - Materials checked per keg (fails gracefully)
#
# Setup:
#   - Storage container with boards, ingots, bottles
#   - Salvage bag with tinker tools + saws (2+ of each to start)
#   - Requires 75+ Tinkering skill (for potion keg assembly)

import API
from lib.crafting import (
    CRAFTING_GUMP,
    PageTracker,
    open_craft_gump,
    wait_for_gump_or_replace_tool,
    start_craft,
    grab_materials_by_weight,
    count_materials,
)
from lib.items import find_salvage_bag, drop_items_to_container
from lib.persistence import load_int, save_int

# === CONFIG ===
BATCH_SIZE = 20  # Number of potion kegs to make

# Tool graphics
TINKER_TOOLS = 0x1EB8
SAW = 0x10E7

# Material graphics (PLACEHOLDERS - verify in game)
INGOTS = 0x1BF2
BOARDS = 0x1BD7
BOTTLES = 0x0F0E  # TODO: verify empty bottle graphic

# Output graphics (PLACEHOLDERS - verify in game)
POTION_KEG_GRAPHIC = 0x1940  # TODO: verify potion keg graphic

# Gump button locations (PLACEHOLDERS - discover in game)
# Format: (page, button)
# TODO: Fill in actual gump locations
BARREL_TAP = (0, 0)  # Tinkering > Parts
BARREL_HOOPS = (0, 0)  # Tinkering > Parts
BARREL_STAVES = (0, 0)  # Carpentry > Other
BARREL_LID = (0, 0)  # Carpentry > Other
KEG = (0, 0)  # Carpentry > Containers
POTION_KEG = (0, 0)  # Tinkering > Assemblies

# Tool crafting recipes (PLACEHOLDERS - discover in game)
# TODO: Fill in actual gump locations for tool recipes
TINKER_TOOLS_RECIPE = (0, 0)  # Tinkering > Tools (2 ingots)
SAW_RECIPE = (0, 0)  # Tinkering > Tools (4 ingots)

# Materials needed per keg
INGOTS_PER_KEG = 7  # 2 for tap + 5 for hoops
BOARDS_PER_KEG = 23  # 15 for staves + 8 for lids
BOTTLES_PER_KEG = 10  # For final assembly

# Tool maintenance
MIN_TOOLS = 2  # Craft more tools if count drops below this


def has_materials_for_one_keg():
    """
    Check if we have enough materials for one complete potion keg.

    Returns:
        True if sufficient materials available, False otherwise
    """
    ingots = count_materials([INGOTS])
    boards = count_materials([BOARDS])
    bottles = count_materials([BOTTLES])

    has_enough = (
        ingots >= INGOTS_PER_KEG
        and boards >= BOARDS_PER_KEG
        and bottles >= BOTTLES_PER_KEG
    )

    if not has_enough:
        API.SysMsg(
            f"Materials: {ingots}/{INGOTS_PER_KEG} ingots, "
            f"{boards}/{BOARDS_PER_KEG} boards, "
            f"{bottles}/{BOTTLES_PER_KEG} bottles",
            33,
        )

    return has_enough


def restock_for_one_keg(storage_serial):
    """
    Grab materials from storage for at least one keg.

    Uses weight-based grabbing to get materials efficiently.

    Args:
        storage_serial: Storage container serial

    Returns:
        True if restocking succeeded, False if storage empty
    """
    API.SysMsg("Restocking materials...", 68)
    grabbed = grab_materials_by_weight(
        storage_serial, [INGOTS, BOARDS, BOTTLES], weight_buffer=20
    )

    if grabbed == 0:
        API.SysMsg("Storage empty - no materials grabbed", 32)
        return False

    API.SysMsg(f"Grabbed materials from storage", 68)
    return True


def craft_items_in_batch(gump_id, page_tracker, tool_type, tool_container, items):
    """
    Craft multiple items using the same gump.

    Args:
        gump_id: Crafting gump ID
        page_tracker: PageTracker instance
        tool_type: Tool graphic ID (for tool replacement)
        tool_container: Container with tools
        items: List of ((page, button), quantity, desc) tuples
    """
    for (page, button), quantity, desc in items:
        for i in range(quantity):
            if API.StopRequested:
                return

            start_craft(gump_id, page_tracker.get_page(page), button)
            wait_for_gump_or_replace_tool(gump_id, tool_type, tool_container)


def count_tools(tool_type, container):
    """
    Count tools of a specific type in a container.

    Args:
        tool_type: Tool graphic ID
        container: Container serial to search

    Returns:
        Number of tools found
    """
    tools = API.FindTypeAll(tool_type, container) or []
    return len(tools)


def craft_tools_if_needed(tool_container, page_tracker):
    """
    Check tool counts and craft more if running low.

    During tinkering phase, ensures minimum stock of tinker tools and saws.
    At 75+ tinkering (required for potion kegs), tool crafting is reliable.

    Args:
        tool_container: Container with tools (salvage bag)
        page_tracker: PageTracker instance
    """
    tinker_count = count_tools(TINKER_TOOLS, tool_container)
    saw_count = count_tools(SAW, tool_container)

    tools_needed = []
    if tinker_count < MIN_TOOLS:
        needed = MIN_TOOLS - tinker_count
        tools_needed.append((TINKER_TOOLS_RECIPE, needed, "tinker tools"))

    if saw_count < MIN_TOOLS:
        needed = MIN_TOOLS - saw_count
        tools_needed.append((SAW_RECIPE, needed, "saw"))

    if tools_needed:
        API.SysMsg(
            f"Low on tools - crafting more (tinkers={tinker_count}, saws={saw_count})",
            68,
        )
        craft_items_in_batch(
            CRAFTING_GUMP, page_tracker, TINKER_TOOLS, tool_container, tools_needed
        )


def craft_one_keg(storage_serial, tool_container, page_tracker):
    """
    Craft one complete potion keg through all phases.

    Workflow:
        1. Tinkering: tap + hoops
        2. Carpentry: 3x staves + 2x lids + keg
        3. Tinkering: potion keg
        4. Move to storage

    Args:
        storage_serial: Storage container serial
        tool_container: Container with tools (salvage bag)
        page_tracker: PageTracker instance

    Returns:
        True if keg completed, False if failed
    """
    # Phase 1: Tinkering (tap + hoops + tool maintenance)
    if not open_craft_gump(TINKER_TOOLS, tool_container, CRAFTING_GUMP):
        API.SysMsg("Failed to open tinkering gump", 32)
        return False

    page_tracker.reset()

    # Check and craft tools if needed (at 75+ tinkering this is reliable)
    craft_tools_if_needed(tool_container, page_tracker)

    # Craft keg components
    craft_items_in_batch(
        CRAFTING_GUMP,
        page_tracker,
        TINKER_TOOLS,
        tool_container,
        [
            (BARREL_TAP, 1, "barrel tap"),
            (BARREL_HOOPS, 1, "barrel hoops"),
        ],
    )

    if API.StopRequested:
        return False

    # Phase 2: Carpentry (staves + lids + keg)
    if not open_craft_gump(SAW, tool_container, CRAFTING_GUMP):
        API.SysMsg("Failed to open carpentry gump", 32)
        return False

    page_tracker.reset()
    craft_items_in_batch(
        CRAFTING_GUMP,
        page_tracker,
        SAW,
        tool_container,
        [
            (BARREL_STAVES, 3, "barrel staves"),
            (BARREL_LID, 2, "barrel lid"),
            (KEG, 1, "keg"),
        ],
    )

    if API.StopRequested:
        return False

    # Phase 3: Tinkering (potion keg assembly)
    if not open_craft_gump(TINKER_TOOLS, tool_container, CRAFTING_GUMP):
        API.SysMsg("Failed to open tinkering gump", 32)
        return False

    page_tracker.reset()
    craft_items_in_batch(
        CRAFTING_GUMP,
        page_tracker,
        TINKER_TOOLS,
        tool_container,
        [(POTION_KEG, 1, "potion keg")],
    )

    if API.StopRequested:
        return False

    # Move finished potion keg to storage immediately
    moved = drop_items_to_container(
        storage_serial, [POTION_KEG_GRAPHIC], source=API.Player.Backpack
    )

    if moved == 0:
        API.SysMsg("Warning: No potion keg found to move!", 33)

    return True


def main():
    # Setup storage container
    storage_key = "ezKegMaker.Storage"
    storage_serial = load_int(storage_key, 0)
    if not storage_serial:
        API.SysMsg("Target storage container (boards, ingots, bottles)", 68)
        storage_serial = API.RequestTarget()
        if storage_serial:
            save_int(storage_key, storage_serial)
        else:
            API.SysMsg("No storage - stopping", 32)
            return

    # Find tool container (salvage bag preferred)
    tool_container = find_salvage_bag() or API.Player.Backpack
    API.SysMsg(
        f"Using tool container: {'salvage bag' if tool_container != API.Player.Backpack else 'backpack'}",
        68,
    )

    # Pre-open storage
    API.UseObject(storage_serial)
    API.Pause(0.3)

    page_tracker = PageTracker()
    completed_kegs = 0

    API.SysMsg(f"=== Starting keg production: {BATCH_SIZE} kegs ===", 68)

    for i in range(BATCH_SIZE):
        if API.StopRequested:
            break

        # Check materials for one keg
        if not has_materials_for_one_keg():
            # Try to restock
            if not restock_for_one_keg(storage_serial):
                API.SysMsg("Storage empty - stopping", 32)
                break

            # Check again after restock
            if not has_materials_for_one_keg():
                API.SysMsg("Not enough materials after restock - stopping", 32)
                break

        API.SysMsg(f"Crafting keg {i + 1}/{BATCH_SIZE}...", 68)

        if craft_one_keg(storage_serial, tool_container, page_tracker):
            completed_kegs += 1
            API.SysMsg(f"Completed keg {completed_kegs}/{BATCH_SIZE}", 68)
        else:
            API.SysMsg("Failed to craft keg - stopping", 32)
            break

    API.SysMsg(f"=== Keg production complete: {completed_kegs} kegs made ===", 68)


main()
