"""
Recall Miner

This script will mine in relative locations according to the resource grid,
recalling home when full, then to the next rune on the runebook. 

It'll try to autodetect which skill to use when recalling, but you can 
configure manually, with magery or chivalry.

Since it uses magic to move around, a 100% LRC suit is recommended.

This script doesn't check for reagents/tithing and only works mining in caves.

REQUIREMENTS:
- Some (50+) Tinkering skill, to make kits and shovels;
- A few (~20) iron ingots, or some shovels;
- A runebook with runes to intersections of the resource grid;
- A rune or default runebook setting to your house;
- A chest on the steps of your house, in reach of the house rune.
"""

### CONFIG ###
shovels_to_keep = 5  # high number to stop less often
use_prospecting = True  # use prospecting tool before mining
use_sturdy = True  # use of study shovels (bod reward)
use_chivalry = False  # true: sacred journey, false: recall
### CONFIG ###

from AutoComplete import *
from lib.util import Hue, head_prompt, safe_cast

SHOVEL = 0x0F39
TOOL_KIT = 0x1EB8
PROSPECTING_TOOL = 0x0FB4
ORE_TYPES = [0x19B7, 0x19B8, 0x19B9, 0x19BA]
TINKER_TOOLS = {'tool kit': 23, 'shovel': 72}
TINKERING_GUMP = 0x38920ABD
RUNEBOOK_GUMP = 89

mining_runebook = Items.FindBySerial(0x404D3431)
# Items.FindBySerial(head_prompt('target your *mining* runebook'))
home_rune = Items.FindBySerial(0x401F5269)
# Items.FindBySerial(head_prompt('target your home rune (or default runebook)'))
home_chest = Items.FindBySerial(0x4066653C)
# Items.FindBySerial(head_prompt('target the chest to store ore in'))

prospected = []
current_rune = 0


def tinkering_menu(tool_num):
    if Gumps.CurrentGump() != TINKERING_GUMP:  # tinkering menu
        Items.UseItemByID(TOOL_KIT, -1)
        Gumps.WaitForGump(TINKERING_GUMP, 2000)

    if not Gumps.LastGumpTextExistByLine(24, "scissors"):
        Gumps.SendAction(TINKERING_GUMP, 15)  # tools tab
        Gumps.WaitForGump(TINKERING_GUMP, 2000)

    Gumps.SendAction(TINKERING_GUMP, tool_num)
    Gumps.WaitForGump(TINKERING_GUMP, 2000)


def make_tools():
    kits = Items.BackpackCount(TOOL_KIT, -1)
    shovels = Items.BackpackCount(SHOVEL, -1 if use_sturdy else 0)

    while kits < 2:  # always keep more than 1 tool kit (if one breaks)
        tinkering_menu(TINKER_TOOLS['tool kit'])
        kits += 1

    while shovels < shovels_to_keep:
        tinkering_menu(TINKER_TOOLS['shovel'])
        shovels += 1

    Gumps.CloseGump(TINKERING_GUMP)


def move_ore():
    ores = filter(lambda f: f.ItemID in ORE_TYPES, Player.Backpack.Contains)
    Player.HeadMessage(Hue.Green, 'Moving ingots to container...')
    for ore in ores:
        Items.Move(ore.Serial, home_chest.Serial, -1)
        Misc.Pause(1000)


def prospect(x, y, z, id):
    if Items.UseItemByID(PROSPECTING_TOOL, 0):
        Target.WaitForTarget(3000)
        Target.TargetExecute(x, y, z, id)
        return

    Misc.SendMessage('unable to use prospecting tool, disabling', Hue.Red)
    global use_prospecting
    use_prospecting = False


def find_tiles():
    x, y = Player.Position.X, Player.Position.Y

    positions = (
        (x - 1, y - 1),  # up
        (x + 1, y - 1),  # right
        (x + 1, y + 1),  # down
        (x - 1, y + 1),  # left
    )

    res = list()
    for x, y in positions:
        land = Statics.GetStaticsTileInfo(x, y, Player.Map)
        if land:
            res.append((x, y, land[0].Z, land[0].StaticID))

    return res


def travel(rune=None):
    if not rune:
        safe_cast('sacred journey' if use_chivalry else 'recall', home_rune)
        return

    Items.UseItem(mining_runebook)
    Gumps.WaitForGump(RUNEBOOK_GUMP, 3000)
    Gumps.SendAction(RUNEBOOK_GUMP, rune)
    Misc.Pause(1250)


def do_the_mining(tile):
    if not Items.UseItemByID(SHOVEL, -1 if use_sturdy else 0):
        make_tools()
        return do_the_mining(tile)

    Target.WaitForTarget(3000, False)
    Target.TargetExecute(*tile)
    Misc.Pause(200)

    if Journal.Search('There is no metal here to mine'):
        Player.HeadMessage(Hue.Yellow, "No ore here!")
        Journal.Clear('There is no metal here to mine')
        return False

    return True


Journal.Clear()  # There is no metal here to mine
while not Player.IsGhost:

    max_weight = Player.MaxWeight
    smelt_weight = max_weight - 60

    rune = current_rune % 16 + (75 if use_chivalry else 50)
    travel(rune)

    Misc.Pause(1250)
    for tile in find_tiles():
        if use_prospecting and not tile in prospected:
            prospected.append(tile)
            prospect(*tile)
            Misc.Pause(575)

        while do_the_mining(tile):
            if Player.Weight >= smelt_weight:
                travel()
                while not Player.InRangeItem(home_chest.Serial, 2):
                    Misc.Pause(50)
                move_ore()
                travel(rune)

    current_rune += 1
    prospected = []
