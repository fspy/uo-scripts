"""Niter Mining for TazUO Legion Scripts.

Mines niter deposits until they disappear.
Niter is used for making black powder/explosives.

Usage:
    Run directly: python gathering/niter.py
    Or import: from gathering.niter import mine_niter
"""

# API is injected at runtime by Legion engine
try:
    import API
except (ImportError, NameError):
    pass

from _lib.utils import Hue, p

# Niter deposit graphics (various states)
NITER_GRAPHICS = [0x1361, 0x1367, 0x1364, 0x1365]
# Pickaxe tool graphic
PICKAXE_TYPE = 0x0E86


def find_niter(range=2):
    """
    Find niter deposit within range.

    Args:
        range: Search range in tiles (default 2)

    Returns:
        Serial of niter deposit or None if not found
    """
    for graphic in NITER_GRAPHICS:
        if API.FindType(graphic, range=range):
            return API.Found
    return None


def find_pickaxe():
    """Find pickaxe in backpack."""
    return API.FindType(PICKAXE_TYPE, API.Backpack)


def mine_niter():
    """
    Mine niter deposits until they disappear or out of pickaxes.

    Requires pickaxe in backpack and niter deposit within 2 tiles.
    """
    pickaxe = find_pickaxe()
    if not pickaxe:
        p("No pickaxe found in backpack!", Hue.Red)
        return

    niter = find_niter()
    if not niter:
        p("No niter deposit found nearby!", Hue.Orange)
        return

    p("Mining niter...", Hue.Cyan)

    while pickaxe and niter and not API.StopRequested:
        API.UseObject(pickaxe)
        if API.WaitForTarget():
            API.Target(niter)  # pyright: ignore
        API.Pause(0.65)

        # Refresh pickaxe and niter references
        pickaxe = find_pickaxe()
        niter = find_niter()

    if not pickaxe:
        p("Out of pickaxes!", Hue.Red)
    elif not niter:
        p("Niter deposit depleted!", Hue.Green)


def main():
    """Main entry point."""
    mine_niter()


main()
