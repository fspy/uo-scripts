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

# Import move_item_robust for moving tools between containers
try:
    from lib.items import move_item_robust
except ImportError:
    pass

# Tool type constants
SCISSORS_TYPE = 0xF9F
TONGS_TYPE = 0x0FBB


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
    crafting_tools_inside = API.FindTypeAll(crafting_tool_type, salvage_bag_serial) or []
    if not crafting_tools_inside:
        return (False, "No crafting tools found inside salvage bag!")
    
    # Ensure salvage tool is outside
    if not ensure_salvage_tool_outside(salvage_bag_serial, salvage_tool_type):
        return (False, "No salvage tools found! Add scissors/tongs to backpack or salvage bag.")
    
    return (True, None)


def get_craft_bracket(skill_value, brackets):
    """
    Find the appropriate craft bracket for current skill level.
    
    Brackets define what item to craft at each skill range. Each bracket
    specifies the maximum skill for that item and the gump page/button.
    
    Args:
        skill_value: Current skill value (e.g., 45.5)
        brackets: List of (max_skill, page, button, description) tuples
                  Example: [(40.0, None, None, "too low"), 
                           (50.0, 15, 2, "scissors")]
    
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
    for max_skill, page, button, desc in brackets:
        if skill_value < max_skill:
            if page is None:
                # Special bracket indicating skill too low for automated training
                API.SysMsg(f"Skill too low: {desc}", 32)
                return None
            return (page, button)
    
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


def craft_item(gump_id, page, button):
    """
    Craft an item via gump with page navigation.
    
    If page is provided, navigates to that page first. Then clicks the
    craft button and waits for confirmation.
    
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
