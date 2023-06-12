from AutoComplete import *

gf = Items.Filter()
gf.Graphics.AddRange([0x0F6C, 0x0DDA])
gf.OnGround = 1
gf.RangeMax = 1

gate = Items.Select(Items.ApplyFilter(gf), 'Nearest')
if gate:
    pos = Player.Position
    Items.Message(gate.Serial, 1150, 'Using Gate!')
    Items.UseItem(gate.Serial)
    while Player.Position == pos:
        if Gumps.CurrentGump() == 3716879466:
            Gumps.SendAction(3716879466, 1)
        Misc.Pause(50)
