from AutoComplete import *
from System import Byte, Int32
from System.Collections.Generic import List


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

    def get(self, criteria):
        self.items = Items.ApplyFilter(self.filter)
        return Items.Select(self.items, criteria)


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

    def get(self, criteria):
        self.mobiles = Mobiles.ApplyFilter(self.filter)
        return Mobiles.Select(self.mobiles, criteria)


filters = {
    'bar': {
        'bottle': ItemFilter(name='A Bottle of Liquor', max_range=2, on_ground=True),
        'pirate': MobileFilter(notorieties=[6], max_range=10),
    },
    'armory': {
        'phylactery': ItemFilter(graphics=[0x4686], hues=[0x081b], max_range=2, on_ground=True),
        'brazier': ItemFilter(name='Purifying Flame', max_range=2, on_ground=True),
        'armor': ItemFilter(name='Cursed Suit of Armor', max_range=2, on_ground=True),
    },
    'orchard': {
        'tree': ItemFilter(graphics=[0x0D01], max_range=1, on_ground=True)
    }
}


def detect_room():
    if Items.FindByID(0x099B, -1, -1, -1):
        return 'bar'
    if Items.FindByName('Cypress Tree', -1, -1, -1):
        return 'orchard'
    if Items.FindByName('Cursed Suit of Armor', -1, -1, -1):
        return 'armory'
    return None


def bar(f):
    bottle = f['bottle'].get('Nearest')
    if not bottle:
        return
    Items.UseItem(bottle)
    Target.WaitForTarget(500)
    while Target.HasTarget():
        mob = f['pirate'].get('Nearest')
        if mob:
            Target.TargetExecute(mob)


def orchard(f):
    tree_hues = [1152, 1153, 1159, 1, 1174, 1283, 1287, 2760]
    trees = Items.FindAllByID(0x0D01, -1, -1, -1)
    pairs = list(zip(trees[::2], trees[1::2]))

    def find_pair(pairs, tree):
        for pair in pairs:
            if pair[0].Serial == tree.Serial or pair[1].Serial == tree.Serial:
                return pair
        return None

    def find_match(pair, tree):
        if pair[0].Serial == tree.Serial:
            return pair[1]
        elif pair[1].Serial == tree.Serial:
            return pair[0]
        return None

    for idx, pair in enumerate(pairs):
        for tree in pair:
            Items.SetColor(tree.Serial, tree_hues[idx])

    pairs_loop = pairs.copy()
    while pairs_loop:
        near_tree = f['tree'].get('Nearest')
        if not near_tree:
            continue

        Items.UseItem(near_tree)
        Player.HeadMessage(90, 'Got apple!')

        tree_pair = find_pair(pairs, near_tree)
        tree_match = find_match(tree_pair, near_tree)
        if not tree_match:
            continue

        Player.TrackingArrow(tree_match.Position.X,
                             tree_match.Position.Y, True)
        while Player.DistanceTo(tree_match) > 2:
            Misc.NoOperation()

        Items.UseItem(Items.FindByID(0x09D0, 0, Player.Backpack.Serial, True))
        Target.WaitForTarget(3000)
        Target.TargetExecute(tree_match)
        Misc.Pause(1000)

        pairs_loop.remove(tree_pair)

    Player.TrackingArrow(0, 0, False)


def armory(f):
    closest_phylactery = f['phylactery'].get('Nearest')
    if closest_phylactery:
        Items.Move(closest_phylactery, Player.Backpack, -1)

    unpurified = Items.FindAllByID(0x4686, 0x081b, Player.Backpack.Serial, -1)
    purified = Items.FindByID(0x4686, 0, Player.Backpack.Serial)

    closest_brazier = f['brazier'].get('Nearest')
    closest_armor = f['armor'].get('Nearest')

    if closest_brazier and unpurified:
        for i in unpurified:
            Items.UseItem(i)
            Target.WaitForTarget(200)
            Target.TargetExecute(closest_brazier)

    if closest_armor and purified:
        Items.UseItem(purified)
        Target.WaitForTarget(1000)
        Target.TargetExecute(closest_armor)


while not Player.IsGhost:
    room = detect_room()
    if room == 'bar':
        bar(filters[room])
    elif room == 'orchard':
        orchard(filters[room])
    elif room == 'armory':
        armory(filters[room])
    Misc.Pause(200)
