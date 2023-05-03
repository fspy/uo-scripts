from urllib import parse, request

from AutoComplete import *
from System import Int32
from System.Collections.Generic import List


class Hue:
    Red = 33
    Yellow = 52
    Green = 63
    Cyan = 1195
    Blue = 98
    Magenta = 128
    White = 1150
    Black = 1
    Gray = 1000


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

    def __init__(self,
                 serials=[],
                 friend=False,
                 max_range=10,
                 line_of_sight=False):
        self.filter = Mobiles.Filter()
        self.filter.Serials = serials
        self.filter.Friend = friend
        self.filter.RangeMax = max_range
        self.filter.CheckLineOfSight = line_of_sight

    def get(self, criteria):
        self.mobiles = Mobiles.ApplyFilter(self.filter)
        return Mobiles.Select(self.mobiles, criteria)


def send_notification(title, message, event='event'):
    data = parse.urlencode({
        'key': 'Ty3zeJ',
        'title': title,
        'msg': message,
        'event': event
    }).encode()
    req = request.Request("https://api.simplepush.io/send", data=data)
    request.urlopen(req).close()


def show_props(item):
    for p in item.Properties:
        print(f'Property {hex(p.Number)}: {p.ToString()}\n')


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
