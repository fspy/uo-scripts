from urllib import parse, request

from AutoComplete import *
from System import Byte, Int32
from System.Collections.Generic import List


class Hue:
    Black = 1
    Blue = 2122
    Cyan = 90
    Gray = 1000
    Green = 63
    Magenta = 128
    Orange = 2736
    Red = 33
    Yellow = 253
    White = 1150


class ItemFilter:
    def __init__(self, graphics=[], name=None, hues=[], max_range=-1, min_range=-1, on_ground=-1):
        self.filter = Items.Filter()
        self.filter.Graphics = List[Int32](graphics)
        self.filter.RangeMin = min_range
        self.filter.RangeMax = max_range
        self.filter.Hues = List[Int32](hues)
        self.filter.OnGround = on_ground

        if name:
            self.filter.Name = name

    def get(self, criteria=None):
        self.items = Items.ApplyFilter(self.filter)
        if criteria:
            return Items.Select(self.items, criteria)
        return self.items


class MobileFilter:
    def __init__(self, serials=[], name=None, friend=False, notorieties=[], max_range=10, line_of_sight=False):
        self.filter = Mobiles.Filter()
        self.filter.Serials = List[Int32](serials)
        self.filter.Friend = friend
        self.filter.RangeMax = max_range
        self.filter.CheckLineOfSight = line_of_sight

        if name:
            self.filter.Name = name

        if notorieties:
            self.filter.Notorieties = List[Byte](bytes(notorieties))

    def get(self, criteria=None):
        self.mobiles = Mobiles.ApplyFilter(self.filter)
        if criteria:
            return Mobiles.Select(self.mobiles, criteria)
        return self.mobiles


def send_notification(title, message, event="event"):
    data = parse.urlencode(
        {"key": "Ty3zeJ", "title": title, "msg": message, "event": event}
    ).encode()
    req = request.Request("https://api.simplepush.io/send", data=data)
    request.urlopen(req).close()


def show_props(item=None):
    if not item:
        item = Items.FindBySerial(Target.PromptTarget())
    for p in item.Properties:
        print(f"Property {hex(p.Number)}: {p.ToString()}\n")


def search_subcontainers(container):
    all = list()
    Items.WaitForContents(container, 5000)
    for item in container.Contains:
        all.append(item)
        if item.IsContainer and "sending" not in item.Name:
            all.extend(search_subcontainers(item))
    return all


def head_prompt(msg, c=55):
    """Shows a head message on target prompt, instead of bottom left."""
    Player.HeadMessage(c, msg)
    return Target.PromptTarget("")


def safe_cast(spell, target=None, wait=3000):
    """Tries to safely cast a spell.

    If we're paralyzed or currently waiting for a target, skip casting.
    It can also be used as a "sphere style" type of casting, if no target
    is provided: Asks for a target first, casting after.
    """
    if not target:
        target = Target.PromptTarget("select a target")
    if Player.Paralized or Target.HasTarget():
        return False
    Spells.Cast(spell)
    Target.WaitForTarget(wait)
    Target.TargetExecute(target)
    return True


def tile_info(x, y, kind):
    land = Statics.GetStaticsLandInfo(x, y, Player.Map)

    if land:
        static_id = land.StaticID
        static_z = land.StaticZ
        is_kind = Statics.GetLandFlag(static_id, kind)
        tile = Statics.GetStaticsTileInfo(x, y, Player.Map)
        if tile.Count == 0:
            static_id = 0x0000
        if not is_kind and tile.Count == 1:
            is_kind = Statics.GetTileFlag(tile[0].StaticID, kind)
            if is_kind:
                static_id = tile[0].StaticID
                static_z = tile[0].StaticZ
        if is_kind:
            return x, y, static_z, static_id
    else:
        tile = Statics.GetStaticsTileInfo(x, y, Player.Map)
        if tile.Count == 1:
            tile = tile[0]
            is_kind = Statics.GetTileFlag(tile.StaticID, kind)
            if is_kind:
                return x, y, static_z, static_id

    return None


def container_item_count(container):
    for line in Items.GetPropStringList(container):
        if "Contents:" not in line:
            continue
        return int(line.split("/")[0].replace("Contents: ", ""))
