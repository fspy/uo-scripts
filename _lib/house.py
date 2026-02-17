"""Housing utilities for TazUO Legion Scripts.

Provides helpers for house management tasks.

Note: API module is injected by Legion engine at runtime as a global.
Import is wrapped in try/except for type hints in editors.
"""

# pyright: basic

# Try to import API for type hints, but don't fail if unavailable
try:
    import API
except (ImportError, NameError):
    pass  # API is injected at runtime by Legion engine

from _lib.utils import Hue, p

# Set Permission gump ID (Co-Owner selection)
SET_PERMISSION_GUMP_ID = 0x29B6C49


def auto_coown():
    """
    Monitors for Set Permission Gump and automatically sets to Co-Owner.

    Run this when interacting with house signs to quickly set permissions.
    Useful for managing multiple characters' access to a house.
    """
    p("Auto Co-Owner: Monitoring for permission gump...", Hue.Cyan)

    while not API.StopRequested:
        if API.HasGump(SET_PERMISSION_GUMP_ID):
            p("Setting permission to Co-Owner!", Hue.Green)
            API.ReplyGump(2)  # Button 2 = Co-Owner
        API.Pause(0.1)
