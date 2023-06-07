"""
Recall Lumberjack
"""


from AutoComplete import *

from lib.util import head_prompt, safe_cast, tile_info

### CONFIG ###
use_chivalry = False  # True: Sacred Journey, False: Recall
# change these to your own or set to None to prompt each time:
axe_serial = 0x411D68D4
runebook_serial = 0x411DDE13
home_rune_serial = 0x401F5269
home_chest_serial = 0x405716D7
### CONFIG ###


WOOD_TYPES = [0x1BD7, 0x3191, 0x318F, 0x3190, 0x2F5F, 0x3199]
RUNEBOOK_GUMP = 89

lumberjack_runebook = Items.FindBySerial(
    runebook_serial or head_prompt('target your *lumberjacking* runebook'))
home_rune = Items.FindBySerial(
    home_rune_serial
    or head_prompt('target your home rune (or default runebook)'))
home_chest = Items.FindBySerial(
    home_chest_serial or head_prompt('target the chest to store ore in'))

current_rune = 0


def move_wood():
    while not Player.InRangeItem(home_chest.Serial, 2):
        Misc.Pause(50)

    wood = filter(lambda f: f.ItemID in WOOD_TYPES, Player.Backpack.Contains)
    for w in wood:
        Items.Move(w.Serial, home_chest.Serial, -1)
        Misc.Pause(625)


def travel(rune=None):
    if not rune:
        safe_cast('sacred journey' if use_chivalry else 'recall', home_rune)
        return

    Items.UseItem(lumberjack_runebook)
    Gumps.WaitForGump(RUNEBOOK_GUMP, 3000)
    Gumps.SendAction(RUNEBOOK_GUMP, rune)
    Misc.Pause(1250) # 2500

    if Journal.SearchByType('Something is blocking the location', 'System'):
        print('something is blocking the rune, go next')
        Journal.Clear('Something is blocking the location')
        travel(rune + 1)


def find_trees():
    def gen_coords():
        return [(Player.Position.X + x, Player.Position.Y + y)
                for x in range(-2, 3) for y in range(-2, 3) if (x, y) != (0, 0)]

    res = list()
    for x, y in gen_coords():
        tile_id = find_tree_tile_id(x, y)
        Statics.Get
        if tile_id:
            res.append((x, y, *tile_id))
    return res


def find_tree_tile_id(x, y):
    tiles = Statics.GetStaticsTileInfo(x, y, Player.Map)
    if len(tiles) == 1 and 'tree' in Statics.GetTileName(tiles[0].StaticID).lower():
        return tiles[0].Z, tiles[0].StaticID
        # return False
    tiles_id = [tile.StaticID for tile in tiles]
    tiles_z = [tile.StaticZ for tile in tiles]
    tiles_names = [Statics.GetTileName(tile_id) for tile_id in tiles_id]

    for tile_id, name, z in zip(tiles_id, tiles_names, tiles_z):
        if "tree" in name.lower():
            return z, tile_id


def gather(tile):
    lhand = Player.GetItemOnLayer('LeftHand')
    if not lhand or lhand.Serial != axe_serial:
        Player.EquipItem(axe_serial)
        Misc.Pause(625)

    Items.UseItem(axe_serial)
    Target.WaitForTarget(3000, False)
    Target.TargetExecute(*tile)
    # Target.TargetResource(axe_serial, 'wood')
    Misc.Pause(50)

    if Journal.Search('not enough wood here to harvest'):
        # Player.HeadMessage(Hue.Yellow, "No ore here!")
        Journal.Clear('not enough wood here to harvest')
        return False

    Misc.Pause(1050)
    return True


def chop():
    logs = Items.FindAllByID(0x1BDD, -1, Player.Backpack.Serial, 2)
    for l in logs:
        Items.UseItem(axe_serial)
        Target.WaitForTarget(3000)
        Target.TargetExecute(l)
        Misc.Pause(626)


Journal.Clear()  # There is no metal here to mine
while not Player.IsGhost:

    max_weight = Player.MaxWeight
    chop_weight = max_weight - 50
    drop_weight = max_weight - 30

    rune = current_rune % 16 + (75 if use_chivalry else 50)
    travel(rune)

    Misc.Pause(1250)
    for tree in find_trees():
        while gather(tree):
            if Player.Weight >= chop_weight:
                chop()
            if Player.Weight >= drop_weight:
                travel()
                move_wood()
                #Misc.Pause(1250)
                travel(rune)
    current_rune += 1
