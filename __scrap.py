from AutoComplete import *

from lib.caster_training import *
from lib.util import tile_info


def useskill(skillname='Tracking', pause=10500):
    while Player.GetSkillValue(skillname) < Player.GetSkillCap(skillname):
        print(skillname)
        Player.UseSkill(skillname)
        if skillname == 'Tracking':
            Gumps.WaitForGump(2976808305, 3000)
            Gumps.SendAction(2976808305, 1)
            Gumps.WaitForGump(2976808305, 3000)
            Gumps.CloseGump(2976808305)
        Misc.Pause(pause)


def vendor_price(price):
    Journal.Clear()
    while not Journal.Search('in a price and description for'):
        Misc.Pause(50)
        continue
    Misc.ResponsePrompt('\n{}\n'.format(price))
    Misc.SendMessage('priced!', 1252)
    Journal.Clear('in a price and description for')
    Misc.Pause(200)


def fish_location():
    if Player.CheckLayer('RightHand'):
        Player.UnEquipItemByLayer('RightHand', 1250)
        Misc.Pause(625)

    pole = Items.FindByID(0x0DC0, -1, Player.Backpack.Serial, True)
    if not pole:
        return

    loc = Target.PromptGroundTarget('Target where to fish!')
    if not loc:
        return

    tile = tile_info(loc, 'Wet')
    if not tile:
        return

    Journal.Clear('seem to be biting here')
    Misc.Pause(600)
    while not Journal.SearchByType('seem to be biting here', 'System'):
        Items.UseItem(pole)
        Target.WaitForTarget(3000)
        Target.TargetExecute(*tile)
        Misc.Pause(8200)

    Misc.Beep()


def mr_white():
    for ps in Items.FindAllByID(0x14F0, 0x0481, Player.Backpack.Serial, False):
        Items.Move(ps.Serial, 0x0000AEFC, 1)
        Misc.Pause(625)

def mine_sand():
    shovel = Items.FindByID(0x0F39, -1, Player.Backpack.Serial, True)
    Target.TargetResource(shovel, 'sand')
    Misc.Pause(200)

#mine_sand()
#useskill('Hiding')

while True: 
    vendor_price(5000)
    Misc.Pause(500)
