"""
Recall Miner

Mines in relative locations according to the resource grid, traveling home when 
full, then returns to the previous location to continue mining. Once that
location is fully depleted, it moves on to the next rune.

Since travel is done using magic (Chivalry/Magery), a 100% LRC suit and/or
enough Tithing points are mandatory, as is, obviously, enough skill to travel.
If using Magery, 64.1 skill is needed to never fail the Recall spell. For
Chivalry, Sacred Journey never fails at 65.0 skill.

To set up the runebook, runes should be marked in grid resource intersections.
A mapping tool that shows the grid when zoomed in, such as ClassicUO's world
map, is needed. It should look like this:

           ║             
  mining * ║ * mining     Runes should be marked in the corner where all
═══════════╬═══════════   sections meet, in order to effectively mine
  mining * ║ * mining     four grid cells without moving.
           ║

Once out of tools, it will make more, given there are ingots in your backpack.
If you keep ingots in the home container, it will take them to make tools.

REQUIREMENTS:
- Enough Tinkering skill to be able to make kits and shovels;
- A runebook filled with runes to resource grid intersections;
- A rune or runebook set as default to your house;
- A container on the steps of your house, in reach of the house rune;
- Some iron ingots to make tools with (with your/in house container).
"""

### CONFIG ###
shovels_to_keep = 5  # high number to stop less often
use_prospecting = True  # use prospecting tool before mining
use_sturdy = True  # use of study shovels (bod reward)
use_chivalry = False  # True: Sacred Journey, False: Recall
# change these to your own or set to None to prompt each time:
runebook_serial = 0x404D3431
home_rune_serial = 0x401F5269
home_chest_serial = 0x4031654D
### CONFIG ###

from AutoComplete import *

from lib.util import Hue, head_prompt, safe_cast

SHOVEL = 0x0F39
TOOL_KIT = 0x1EB8
PROSPECTING_TOOL = 0x0FB4
ORE_TYPES = [
    0x19B7, 0x19B8, 0x19B9, 0x19BA, 0x0F28, 0x3192, 0x3193, 0x3194, 0x3195,
    0x3196, 0x3197, 0x3198, 0x1779
]
IRON_INGOT = 0x1BF2
TINKER_TOOLS = {'tool kit': 23, 'shovel': 72}
TINKERING_GUMP = 0x38920ABD
RUNEBOOK_GUMP = 89

mining_runebook = Items.FindBySerial(
    runebook_serial or head_prompt('target your *mining* runebook'))
home_rune = Items.FindBySerial(
    home_rune_serial
    or head_prompt('target your home rune (or default runebook)'))
home_chest = Items.FindBySerial(
    home_chest_serial or head_prompt('target the chest to store ore in'))
    
    
Journal.FilterText('Where do you wish to dig?')
Journal.FilterText('loosen some rocks but fail')
Journal.FilterText('ore and put it in your backpack')
Journal.FilterText('no metal here to mine')
Journal.FilterText('worn out your tool!')

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
    Gumps.WaitForGump(TINKERING_GUMP, 1250)
    if Gumps.CurrentGump == TINKERING_GUMP:
        Gumps.CloseGump(TINKERING_GUMP)


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


def get_ingots():
    iron_amount = (shovels_to_keep + 1) * 4  # shovels + 2 kits
    backpack_iron = Items.BackpackCount(IRON_INGOT, 0)
    if backpack_iron >= iron_amount:
        return

    Items.WaitForContents(home_chest.Serial, 2000)
    Misc.Pause(625)
    chest_iron = Items.FindByID(IRON_INGOT, 0, home_chest.Serial, False)
    if chest_iron and chest_iron.Amount > iron_amount:
        Items.Move(chest_iron, Player.Backpack, iron_amount)
        Misc.Pause(1250)


def move_ore():
    ores = filter(lambda f: f.ItemID in ORE_TYPES, Player.Backpack.Contains)
    for ore in ores:
        Items.Move(ore.Serial, home_chest.Serial, -1)
        Misc.Pause(1250)


def prospect(x, y, z, id):
    if Items.UseItemByID(PROSPECTING_TOOL, 0):
        Target.WaitForTarget(3000)
        Target.TargetExecute(x, y, z, id)
        return

    # Misc.SendMessage('unable to use prospecting tool, disabling', Hue.Red)
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

    if Journal.SearchByType('Something is blocking the location', 'System'):
        print('something is blocking the rune, go next')
        travel(rune + 1)


def do_the_mining(tile):
    if not Items.UseItemByID(SHOVEL, -1 if use_sturdy else 0):
        make_tools()
        return do_the_mining(tile)

    Target.WaitForTarget(3000, False)
    Target.TargetExecute(*tile)
    Misc.Pause(200)

    if Journal.Search('There is no metal here to mine'):
        # Player.HeadMessage(Hue.Yellow, "No ore here!")
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
                get_ingots()
                travel(rune)

    current_rune += 1
    prospected = []
