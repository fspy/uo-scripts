from AutoComplete import *
from System.Collections.Generic import List
from System import Int32


class Hue:
    Red = 1,
    Yellow = 1,
    Green = 1,
    Cyan = 1,
    Blue = 1,
    Magenta = 1,
    Red = 1,
    White = 1,
    Black = 1,
    Gray = 1


class Filter:

    def __init__(self,
                 serials=[],
                 graphics=[],
                 hues=[],
                 name="",
                 min_range=-1,
                 max_range=-1):
        pass


class ItemFilter:

    def __init__(self, graphics=[], max_range=-1, min_range=-1, on_ground=-1):
        self.filter = Items.Filter()
        self.filter.Graphics = List[Int32](graphics)
        self.filter.RangeMin = min_range
        self.filter.RangeMax = max_range
        self.filter.OnGround = on_ground

    def get(self, criteria):
        self.items = Items.ApplyFilter(self.filter)
        return Items.Select(self.items, criteria)


class MobileFilter:

    def __init__(self, serials=[], friend=False, line_of_sight=False):
        self.filter = Mobiles.Filter()
        self.filter.Serials = serials
        self.filter.Friend = friend
        self.filter.CheckLineOfSight = line_of_sight

    def get(self, criteria):
        self.mobiles = Mobiles.ApplyFilter(self.filter)
        return Mobiles.Select(self.mobiles, criteria)


def head_prompt(msg, c=55):
    """Shows a head message on target prompt, instead of bottom left."""
    Player.HeadMessage(c, msg)
    return Target.PromptTarget('')


def safe_cast(spell, target=None, wait=3000):
    """Tries to safely cast a spell.
    
    If we're paralyzed or currently waiting for a target, skip casting.
    It can also be used as a "sphere style" type of casting, if no target
    is provided: Asks for a target first, casting after.
    """
    if not target:
        target = Target.PromptTarget('select a target')
    if Player.Paralized or Target.HasTarget():
        return False
    Spells.Cast(spell)
    Target.WaitForTarget(wait)
    Target.TargetExecute(target)
    return True
