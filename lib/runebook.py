"""Shared runebook interaction and travel utilities for Legion scripts.

Provides:
- Runebook class for gump-based recall to specific rune indices
- Travel utility functions (wait for travel, cast-and-target recall)

Based on button formula from PlayTazUO/PublicLegionScripts RunebookRecaller.py

Note: API module is injected by Legion engine at runtime as a global.
Import is wrapped in try/except for type hints in editors.
"""

# pyright: basic
import time

# Try to import API for type hints, but don't fail if unavailable
try:
    import API
except (ImportError, NameError):
    pass  # API is injected at runtime by Legion engine

# Runebook constants
RUNEBOOK_GRAPHIC = 0x22C5
RUNEBOOK_GUMP_ID = 0x59

# Button formula: recall_button = base + (rune_index * stride)
# Tested on this shard: recall button for rune N = 50 + N
RECALL_BUTTON_BASE = 50
RECALL_BUTTON_STRIDE = 1

# Sacred Journey assumed to be offset by 1 (needs verification)
SJ_BUTTON_BASE = 6
SJ_BUTTON_STRIDE = 6

# Travel failure detection messages
# Note: There are no reliable success messages - only check for failures and position change
TRAVEL_FAIL_MSGS = [
    "You have not yet recovered",
    "Spell fizzles",
    "Target is blocked",
    "You are not powerful enough",
]


class Runebook:
    """Interact with a runebook via its gump."""
    
    def __init__(self, serial: int):
        """
        Initialize a Runebook wrapper.
        
        Args:
            serial: The runebook item serial
        """
        self.serial = serial
    
    def open(self, timeout: float = 2.0) -> bool:
        """
        Open the runebook gump.
        
        Args:
            timeout: How long to wait for gump to appear
            
        Returns:
            True if gump opened successfully
        """
        API.UseObject(self.serial)
        return API.WaitForGump(RUNEBOOK_GUMP_ID, timeout)
    
    def close(self) -> None:
        """Close the runebook gump if open."""
        if API.HasGump(RUNEBOOK_GUMP_ID):
            API.CloseGump(RUNEBOOK_GUMP_ID)
    
    def recall_to_index(self, index: int) -> bool:
        """
        Recall to rune at index (0-15).
        Opens gump if needed, clicks recall button.
        
        Args:
            index: Rune index (0-15)
            
        Returns:
            True if button was clicked (not if travel succeeded)
        """
        if index < 0 or index > 15:
            API.SysMsg(f"Invalid rune index: {index}", 32)
            return False
        
        # Open gump if not already open
        if not API.HasGump(RUNEBOOK_GUMP_ID):
            if not self.open():
                API.SysMsg("Failed to open runebook", 32)
                return False
        
        # Calculate and click recall button
        button_id = RECALL_BUTTON_BASE + (index * RECALL_BUTTON_STRIDE)
        result = API.ReplyGump(button_id, RUNEBOOK_GUMP_ID)
        
        # Give server time to process
        API.Pause(0.5)
        return result
    
    def sacred_journey_to_index(self, index: int) -> bool:
        """
        Sacred Journey (Chivalry) to rune at index (0-15).
        
        Args:
            index: Rune index (0-15)
            
        Returns:
            True if button was clicked (not if travel succeeded)
        """
        if index < 0 or index > 15:
            API.SysMsg(f"Invalid rune index: {index}", 32)
            return False
        
        # Open gump if not already open
        if not API.HasGump(RUNEBOOK_GUMP_ID):
            if not self.open():
                API.SysMsg("Failed to open runebook", 32)
                return False
        
        # Calculate and click Sacred Journey button
        button_id = SJ_BUTTON_BASE + (index * SJ_BUTTON_STRIDE)
        result = API.ReplyGump(button_id, RUNEBOOK_GUMP_ID)
        
        # Give server time to process
        API.Pause(0.5)
        return result


def wait_for_travel(timeout: float = 5.0) -> bool:
    """
    Wait for recall/SJ travel to complete.
    Monitors journal for failure messages and position changes.
    
    Note: There are no reliable success messages for travel spells.
    Success is detected by position change. Failure is detected by
    journal messages (fizzle, encumbered, blocked, etc.).
    
    Args:
        timeout: Maximum time to wait for travel
        
    Returns:
        True if position changed (travel succeeded), False if failed or timeout
    """
    start_pos = (API.Player.X, API.Player.Y)
    deadline = time.time() + timeout
    
    while time.time() < deadline and not API.StopRequested:
        # Check for failure messages (fizzle, encumbered, blocked, etc.)
        if API.InJournalAny(TRAVEL_FAIL_MSGS):
            return False
        
        # Check if position changed significantly
        if abs(API.Player.X - start_pos[0]) > 5 or abs(API.Player.Y - start_pos[1]) > 5:
            return True
        
        API.Pause(0.1)
    
    # Timeout - position didn't change
    return False


def recall_and_target(target_serial: int, use_sacred_journey: bool = False) -> bool:
    """
    Cast Recall or Sacred Journey spell and target an item (rune/runebook).
    Used for simple "go home" type travel where we just target the item.
    
    Args:
        target_serial: Serial of the rune or runebook to target
        use_sacred_journey: If True, use Sacred Journey (Chivalry), else Recall (Magery)
        
    Returns:
        True if travel succeeded
    """
    spell = "Sacred Journey" if use_sacred_journey else "Recall"
    
    API.ClearJournal()
    API.CastSpell(spell)
    
    if not API.WaitForTarget(timeout=5):
        API.SysMsg(f"{spell} failed - no target cursor", 32)
        return False
    
    API.Target(target_serial)  # type: ignore
    return wait_for_travel()


def recall_with_retry(target_serial: int, max_retries: int = 3, retry_delay: float = 2.0, use_sacred_journey: bool = False) -> bool:
    """
    Recall with automatic retry on failure.
    
    Attempts recall/sacred journey multiple times, waiting between attempts
    for cooldowns to expire or recover from fizzles/interrupts.
    
    Args:
        target_serial: Serial of rune/runebook to target
        max_retries: Maximum number of attempts (default 3)
        retry_delay: Seconds to wait between retries (default 2.0)
        use_sacred_journey: Use Sacred Journey instead of Recall (default False)
    
    Returns:
        True if travel succeeded, False if all attempts failed
    
    Example:
        if recall_with_retry(home_rune.Serial, max_retries=5, retry_delay=3.0):
            API.SysMsg("Made it home!")
        else:
            API.SysMsg("Failed to recall home", 32)
    """
    for attempt in range(1, max_retries + 1):
        API.ClearJournal()
        if recall_and_target(target_serial, use_sacred_journey):
            return True
        if attempt < max_retries:
            API.Pause(retry_delay)
    return False


def find_runebook_in_backpack() -> int:
    """
    Find the first runebook in the player's backpack.
    
    Returns:
        Runebook serial, or 0 if not found
    """
    book = API.FindType(RUNEBOOK_GRAPHIC, API.Backpack)
    if book:
        return book.Serial
    return 0
