"""
Shadowguard Helper
"""

# Settings
bot_mode = True  # loops the script
auto_target = True  # automatically targets mobs @ bar
LAG = 150
# Settings

from AutoComplete import *
from System.Collections.Generic import List
from System import Byte

colors = {
    'green': 65,
    'cyan': 90,
    'orange': 43,
    'red': 1100,
    'yellow': 52,
    'white': 1150
}

item_filter = Items.Filter()
item_filter.RangeMax = 2


def closest_item(item_name, on_ground=False):
    item_filter.Name = item_name
    item_filter.OnGround = on_ground
    results = Items.ApplyFilter(item_filter)
    return Items.Select(results, 'Nearest')


def closest_mobile(mobile_name=None, notoriety=[3, 4, 5, 6], max_range=2):
    mobile_filter = Mobiles.Filter()

    if mobile_name:
        mobile_filter.Name = mobile_name
    mobile_filter.Notorieties = List[Byte](bytes(notoriety))
    mobile_filter.RangeMax = max_range
    results = Mobiles.ApplyFilter(mobile_filter)
    return Mobiles.Select(results, 'Nearest')


def detect_room():
    if Items.FindByID(0x099B, -1, -1, -1):
        return 'bar'
    if Items.FindByName('Cypress Tree', -1, -1, -1):
        return 'orchard'
    if Items.FindByName('Cursed Suit of Armor', -1, -1, -1):
        return 'armory'
    if Items.FindByID(0x9BFF, -1, -1, -1):
        return 'canals'

    return None


def bar(auto=False):
    if not auto:  # try to use a bottle, targetting done by user
        return Items.UseItemByID(0x099B, -1)

    # auto finds target and throws bottles
    target = closest_mobile(notoriety=[6], max_range=10)  # closest "murderer"
    if not target or not Items.UseItemByID(0x099B, -1):
        # Misc.SendMessage('no targets nearby, cancelling', colors['orange'])
        Target.Cancel()
        return

    Mobiles.Message(target, colors['cyan'], '* Target *')
    Target.WaitForTarget(LAG)  # idk?
    Target.TargetExecute(target)


def orchard(auto=False):
    apple = Items.FindByID(0x09D0, -1, Player.Backpack.Serial, True)
    if not apple:
        return

    Player.HeadMessage(colors['green'], apple.Name)
    Items.UseItem(apple)


def armory(auto=False):
    unpurified = Items.FindAllByID(0x4686, 0x081b, Player.Backpack.Serial, -1)
    purified = Items.FindByID(0x4686, 0, Player.Backpack.Serial)

    closest_brazier = closest_item('Purifying Flames', True)
    closest_armor = closest_item('Cursed Suit of Armor', True)

    if closest_brazier and unpurified:
        # Player.HeadMessage(colors['orange'], 'Purifying!')
        for i in unpurified:
            Items.UseItem(i)
            Target.WaitForTarget(LAG)
            Target.TargetExecute(closest_brazier)

    if closest_armor and purified:
        # Player.HeadMessage(colors['cyan'], 'Destroying statue!')
        Items.UseItem(purified)
        Target.WaitForTarget(1000)
        Target.TargetExecute(closest_armor)


while not Player.IsGhost:
    room = detect_room()
    if room == 'bar':
        bar(auto_target)
    elif room == 'orchard':
        orchard(auto_target)
    elif room == 'armory':
        armory(auto_target)

    Misc.Pause(LAG)

    if not bot_mode:
        break
"""


#sort canal piece if found
if canal:
    if canal[0].ItemID == 0x9BEF:
        Items.Move(canal[0].Serial, Player.Backpack.Serial, 1, 1, 1)  #top left
    elif canal[0].ItemID == 0x9BF4:
        Items.Move(canal[0].Serial, Player.Backpack.Serial, 1, 95,
                   1)  #top middle
    elif canal[0].ItemID == 0x9BEB:
        Items.Move(canal[0].Serial, Player.Backpack.Serial, 1, 150,
                   1)  #top middle
    elif canal[0].ItemID == 0x9BF8:
        Items.Move(canal[0].Serial, Player.Backpack.Serial, 1, 1,
                   150)  #top middle
    elif canal[0].ItemID == 0x9BE7:
        Items.Move(canal[0].Serial, Player.Backpack.Serial, 1, 95,
                   150)  #top middle
    elif canal[0].ItemID == 0x9BFC:
        Items.Move(canal[0].Serial, Player.Backpack.Serial, 1, 150,
                   150)  #top middle

"""