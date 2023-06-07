import sys

def find_pole():
    pole = Player.GetItemOnLayer('RightHand')
    if pole and pole.ItemID == 0x0DC0:
        return pole
    else:
        pole = Items.FindByID(0x0DC0, -1, Player.Backpack.Serial)
        if pole:
            return pole
        else:
            Misc.SendMessage('no fishing pole')
            sys.exit(99)
            
def get_tile(loc):
    tiles = Statics.GetStaticsTileInfo(loc.X, loc.Y, Player.Map)
    if len(tiles) != 0 and tiles[0].StaticID != 0:
        return tiles[0].StaticZ, tiles[0].StaticID
    return -5, 0

def fish():
    pole = find_pole()
    while not Journal.Search("seem to be biting here."):
        Items.UseItem(pole)
        Target.WaitForTarget(1500)
        Target.TargetExecute(target.X, target.Y, *get_tile(target))
        Misc.Pause(250)
        if Journal.Search("seem to be biting here."):
            break
        Misc.Pause(8250)
    Player.HeadMessage(1311, 'No fish here!')
    Misc.Beep()
    sys.exit(99)

    
target = Target.PromptGroundTarget('Select location to fish')

Journal.Clear()
while True:
    fish()
