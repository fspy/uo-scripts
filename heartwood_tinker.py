from AutoComplete import *

npc_serial = 0x00066EB2


def toggle_quest(id):
    Misc.UseContextMenu(Player.Serial, 'toggle quest item', 3000)
    items = Items.FindAllByID(id, 0, Player.Backpack.Serial, True)
    for item in items[:10]:
        Target.WaitForTarget(3000)
        Target.TargetExecute(item)
        Misc.Pause(200)
    Target.Cancel()
    if not items:
        return False
    return True


def turnin():
    Mobiles.UseMobile(npc_serial)
    Gumps.WaitForGump(1280077232, 3000)
    Gumps.SendAction(1280077232, 8)
    Gumps.WaitForGump(1280077232, 3000)
    Gumps.SendAction(1280077232, 5)


def make_last():
    while True:
        Gumps.WaitForGump(949095101, 10000)
        Gumps.SendAction(949095101, 21)
        Gumps.WaitForGump(949095101, 3000)
        if Gumps.CurrentGump() != 949095101:
            Items.UseItemByID(0x1EB8, 0)


def get_quest():
    while Gumps.CurrentGump() != 1280077232 or Gumps.LastGumpGetLine(1) != "Necessity's Mother":
        Mobiles.UseMobile(npc_serial)
        Misc.Pause(600)
    Gumps.SendAction(1280077232, 4)


while True:
    get_quest()
    if toggle_quest(0x1EB8):
        turnin()
    Misc.Pause(1000)
