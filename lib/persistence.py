"""Shared persistent variable utilities for Legion scripts.

Provides helpers for loading/saving persistent integers and setting up
items that need to persist across script runs.

Note: API module is injected by Legion engine at runtime as a global.
Import is wrapped in try/except for type hints in editors.
"""

# pyright: basic
# Try to import API for type hints, but don't fail if unavailable
try:
    import API
except (ImportError, NameError):
    pass  # API is injected at runtime by Legion engine


def load_int(key: str, default: int = 0, scope=None) -> int:
    """
    Load a persistent integer variable.
    Accepts either decimal or hex strings.
    
    Args:
        key: Persistent variable name
        default: Default value if not found or invalid
        scope: PersistentVar scope (defaults to Char)
    
    Returns:
        Integer value or default if not found/invalid
    """
    if scope is None:
        scope = API.PersistentVar.Char
    
    value_str = API.GetPersistentVar(key, str(default), scope)
    try:
        value = int(str(value_str).strip(), 0)
    except Exception:
        return default
    
    if value < 0:
        return default
    
    return value


def save_int(key: str, value: int, scope=None) -> None:
    """
    Save a persistent integer variable.
    
    Args:
        key: Persistent variable name
        value: Integer value to save
        scope: PersistentVar scope (defaults to Char)
    """
    if scope is None:
        scope = API.PersistentVar.Char
    
    API.SavePersistentVar(key, str(int(value)), scope)


def setup_target(key: str, prompt: str, verify_in_range: bool = True, scope=None) -> int:
    """
    Load persisted serial, verify it exists, or prompt user to target.
    
    This helper loads a saved serial number, optionally verifies the item/mobile
    is still accessible, and prompts the user to re-target if needed.
    
    Args:
        key: Persistent variable name
        prompt: Message to display when prompting for target
        verify_in_range: If True, verify item/mobile exists before using saved serial.
                        If False, trust the saved serial even if out of range.
        scope: PersistentVar scope (defaults to Char)
    
    Returns:
        Serial number, or 0 if setup failed
    """
    if scope is None:
        scope = API.PersistentVar.Char
    
    # Try loading persisted serial
    saved = API.GetPersistentVar(key, "0", scope)
    if saved and saved != "0":
        try:
            serial = int(saved)
            
            if not verify_in_range:
                # Trust the saved serial without verification
                API.SysMsg(f"Using saved {key}: 0x{serial:X}", 946)
                return serial
            
            # Verify item or mobile exists
            item = API.FindItem(serial)
            if item:
                API.SysMsg(f"Using saved {key}: 0x{serial:X}", 946)
                return serial
            
            mob = API.FindMobile(serial)
            if mob:
                API.SysMsg(f"Using saved {key}: 0x{serial:X}", 946)
                return serial
            
            # Not found - fall through to prompt
            API.SysMsg(f"Saved {key} not found - please re-target", 32)
        except ValueError:
            pass  # Invalid serial, fall through to prompt
    
    # Ask user to target
    API.SysMsg(prompt, 32)
    target = API.RequestTarget(timeout=30.0)
    if not target:
        API.SysMsg(f"No target selected for {key}", 32)
        return 0
    
    # Save and return
    API.SavePersistentVar(key, str(target), scope)
    API.SysMsg(f"{key} saved: 0x{target:X}", 946)
    return target
