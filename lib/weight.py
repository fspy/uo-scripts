"""Shared weight management utilities for Legion scripts.

Provides helpers for checking player weight status to avoid being stuck
when recalling or traveling.

Note: API module is injected by Legion engine at runtime as a global.
Import is wrapped in try/except for type hints in editors.
"""

# pyright: basic
# Try to import API for type hints, but don't fail if unavailable
try:
    import API
except (ImportError, NameError):
    pass  # API is injected at runtime by Legion engine


def is_heavy(buffer: int = 50) -> bool:
    """
    Check if player is near maximum weight.
    
    Args:
        buffer: Weight buffer in stones (default 50)
                Player is considered heavy when within this many stones of max
    
    Returns:
        True if player weight >= (max_weight - buffer)
    """
    if not API.Player or API.Player.WeightMax is None or API.Player.Weight is None:
        return False
    return API.Player.Weight >= (API.Player.WeightMax - buffer)


def is_overweight() -> bool:
    """
    Check if player is over maximum weight.
    
    When overweight, the player cannot recall or use gates.
    
    Returns:
        True if player weight > max_weight
    """
    if not API.Player or API.Player.WeightMax is None or API.Player.Weight is None:
        return False
    return API.Player.Weight > API.Player.WeightMax
