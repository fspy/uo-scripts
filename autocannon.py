import re

from AutoComplete import *


def get_gumpid(item):
    Items.UseItem(item)
    Gumps.WaitForGump(0, 3000)
    return Gumps.CurrentGump()


def buttons(gumpid):
    raw = Gumps.GetGumpRawData(gumpid)
    return re.findall(r'{ button.+? (\d+) }', raw)


def shoot(gumpid):
    if not Gumps.HasGump(gumpid):
        return
    if '1' in buttons(gumpid):
        Gumps.SendAction(gumpid, 1)
        Player.HeadMessage(1311, 'Preparing...')
        while '6' not in buttons(gumpid):
            Misc.Pause(500)
    if '6' in buttons(gumpid):
        Player.HeadMessage(1311, 'Firing!')
        Gumps.SendAction(gumpid, 6)
        Misc.Pause(1500)


def run():
    cannon = Items.FindBySerial(Target.PromptTarget('Target the Cannon', 33))
    Misc.UseContextMenu(cannon.Serial, 'repair weapon', 3000)
    Misc.Pause(200)
    gumpid = get_gumpid(cannon)
    while True:
        shoot(gumpid)
        Misc.Pause(500)


run()
