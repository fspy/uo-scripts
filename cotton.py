"""
All-in-one cotton picker and cloth maker!

Make sure to add bales of cotton (0x0DF9) to the scavenger!
If this script finds a `cotton plant` nearby, it will try to run to it and
gather it. It currently doesn't check for weight, so watch out.

If it finds cotton or thread in the player's backpack, it will try to find a
spinning wheel and loom to make cloth, also without checking for weight.

There's a small chance that you'll find yourself making cloth and there is a
cotton plant nearby,
"""
# will find cotton nearby, walk to it, use it, scavenge it, repeat.
# don't forget to add 0x0DF9 to scavenger!

from AutoComplete import *
from lib.util import Hue, ItemFilter

cotton_item_id = 0x0DF9
thread_item_id = 0x0FA0
cotton_ids = (0x0C51, 0x0C52, 0x0C53, 0x0C54)
wheel_ids = [0x1019, 0x101A, 0x101B, 0x101C]
loom_ids = [0x105F, 0x1060, 0x1061, 0x1062]

wheel_filter = ItemFilter(wheel_ids, max_range=2, on_ground=1)
loom_filter = ItemFilter(loom_ids, max_range=2, on_ground=1)


def use_on_nearest_target(item, target_filter, full_amount=False):

    def use(item, target):
        Items.UseItem(item)
        Target.WaitForTarget(3000)
        Target.TargetExecute(target)
        Misc.Pause(50)

    target = target_filter.get('Nearest')
    if not target:
        return

    if not full_amount:
        return use(item, target)

    for _ in range(item.Amount):
        use(item, target)


def make_cloth():
    cotton = Items.FindByID(cotton_item_id, -1, Player.Backpack.Serial)
    if cotton:
        use_on_nearest_target(cotton, wheel_filter)
    thread = Items.FindByID(thread_item_id, -1, Player.Backpack.Serial)
    if thread:
        use_on_nearest_target(thread, loom_filter, True)


def distance(a, b):
    ax, ay = a.Position.X, a.Position.Y
    bx, by = b.Position.X, b.Position.Y
    return Misc.Distance(ax, ay, bx, by)


def nearest_cotton():
    nearby_cotton = [
        item for id in cotton_ids
        for item in Items.FindAllByID(id, -1, -1, 16)
    ]
    return next(
        iter(sorted(nearby_cotton, key=lambda i: distance(Player, i))), None)


def pick_cotton():
    cotton = nearest_cotton()
    if not cotton:
        if not Timer.Check('cottonwarning'):
            Player.HeadMessage(Hue.Red, "Didn't find any cotton nearby!")
            Timer.Create('cottonwarning', 10000)
        Misc.Pause(50)
        return

    Player.HeadMessage(Hue.Green, 'Found some cotton!')
    Items.Message(cotton, Hue.White, 'Over here!')
    while distance(cotton, Player) > 2:
        Player.PathFindTo(cotton.Position)
        Misc.Pause(2000)
    
    Items.UseItem(cotton)
    Misc.Pause(625)

Timer.Create('cottonwarning', 1)
while not Player.IsGhost:
    pick_cotton()
    make_cloth()
    Misc.Pause(50)