from AutoComplete import *

from lib.util import Hue

axe_serial = Player.GetItemOnLayer('LeftHand')


def find_trees():
    def gen_coords():
        return [(Player.Position.X + x, Player.Position.Y + y)
                for x in range(-2, 3) for y in range(-2, 3) if (x, y) != (0, 0)]

    res = list()
    for x, y in gen_coords():
        tile_id = find_tree_tile_id(x, y)
        if tile_id:
            res.append((x, y, *tile_id))
    return res


def find_tree_tile_id(x, y):
    tiles = Statics.GetStaticsTileInfo(x, y, Player.Map)
    if len(tiles) == 1 and 'tree' in Statics.GetTileName(tiles[0].StaticID).lower():
        return tiles[0].Z, tiles[0].StaticID
    tiles_id = [tile.StaticID for tile in tiles]
    tiles_z = [tile.StaticZ for tile in tiles]
    tiles_names = [Statics.GetTileName(tile_id) for tile_id in tiles_id]

    for tile_id, name, z in zip(tiles_id, tiles_names, tiles_z):
        if "tree" in name.lower():
            return z, tile_id


def gather(tile):
    Items.UseItem(axe_serial)
    Target.WaitForTarget(3000, False)
    Target.TargetExecute(*tile)
    Misc.Pause(50)

    # TODO read journal lines
    if Journal.Search('not enough wood here to harvest'):
        Journal.Clear('not enough wood here to harvest')
        return False
    elif Journal.Search('use an axe on that'):
        Journal.Clear('use an axe on that')
        return False
    elif Journal.Search('is too far away'):
        Journal.Clear('is too far away')
        return False
    Misc.Pause(225)
    return True


def chop():
    logs = Items.FindAllByID(0x1BDD, -1, Player.Backpack.Serial, 0)
    # print(f'chopping {logs}')
    for l in logs:
        Items.UseItem(axe_serial)
        Target.WaitForTarget(3000)
        Target.TargetExecute(l)
        Misc.Pause(625)


def drop():
    boards = Items.FindAllByID(0x1BD7, -1, Player.Backpack.Serial, 0)
    # print(f'dropping {boards}')
    for w in boards:
        Items.MoveOnGround(w, 0, Player.Position.X + 1,
                           Player.Position.Y + 1, Player.Position.Z)
        # Items.DropItemGroundSelf(w, 0)
        Misc.Pause(625)


Journal.Clear()  # There is no metal here to mine
Journal.FilterText('not enough wood here to harvest')
Journal.FilterText('do you want to use this item on')
while not Player.IsGhost:
    max_weight = Player.MaxWeight
    chop_weight = max_weight - 50
    drop_weight = max_weight - 30
    for tree in find_trees():
        while gather(tree):
            if Player.Weight >= chop_weight:
                chop()
            if Player.Weight >= drop_weight:
                drop()
    Player.HeadMessage(Hue.Yellow, "No wood here!")
