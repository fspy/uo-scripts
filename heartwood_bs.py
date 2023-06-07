from AutoComplete import *

beetle_serial = 0x00008701
npc_serial = 0x00065CF4


def use_tool():
    if Gumps.CurrentGump() != 949095101:
        Items.UseItemByID(0x0FBB, -1)
        Gumps.WaitForGump(949095101, 3000)


def make_heater_shields():
    # heater shield - 0x1B76 - 10
    use_tool()
    Gumps.SendAction(949095101, 15)
    Gumps.WaitForGump(949095101, 3000)
    Gumps.SendAction(949095101, 16)
    Gumps.WaitForGump(949095101, 3000)

    while Items.BackpackCount(0x1B76, -1) < 10:
        use_tool()
        Gumps.SendAction(949095101, 21)
        Gumps.WaitForGump(949095101, 3000)

    toggle_quest(0x1B76)


def make_broadswords():
    # broadsword - 0x0F5E - 12
    use_tool()
    Gumps.SendAction(949095101, 22)
    Gumps.WaitForGump(949095101, 3000)
    Gumps.SendAction(949095101, 9)
    Gumps.WaitForGump(949095101, 3000)

    while Items.BackpackCount(0x0F5E, -1) < 12:
        use_tool()
        Gumps.SendAction(949095101, 21)
        Gumps.WaitForGump(949095101, 3000)

    toggle_quest(0x0F5E)


def make_bascinets():
    # bascinet - 0x140C - 15
    use_tool()
    Gumps.SendAction(949095101, 8)
    Gumps.WaitForGump(949095101, 3000)
    Gumps.SendAction(949095101, 2)
    Gumps.WaitForGump(949095101, 3000)

    while Items.BackpackCount(0x140C, -1) < 15:
        use_tool()
        Gumps.SendAction(949095101, 21)
        Gumps.WaitForGump(949095101, 3000)

    toggle_quest(0x140C)


def toggle_quest(id):
    Misc.UseContextMenu(Player.Serial, 'toggle quest item', 3000)
    items = Items.FindAllByID(id, 0, Player.Backpack.Serial, True)
    for item in items:
        Target.WaitForTarget(3000)
        Target.TargetExecute(item)
        Misc.Pause(200)
    Target.Cancel()


def turnin():
    Mobiles.UseMobile(0x00065CF4)
    Gumps.WaitForGump(1280077232, 3000)
    Gumps.SendAction(1280077232, 8)
    Gumps.WaitForGump(1280077232, 3000)
    Gumps.SendAction(1280077232, 5)


def make_quest_items():
    if Gumps.CurrentGump() != 1280077232:  # quest gump
        raise Exception('invalid gump')

    l = Gumps.LastGumpGetLine(1)  # quest name
    if l == 'The Bulwark':
        make = make_heater_shields
    elif l == 'Nothing Fancy':
        make = make_bascinets
    elif l == 'Cuts Both Ways':
        make = make_broadswords
    else:
        raise Exception('invalid quest')

    Gumps.SendAction(1280077232, 4)  # accept quest
    make()


def restock_ingots():
    beetle = Mobiles.FindBySerial(beetle_serial)
    Items.WaitForContents(beetle.Backpack, 3000)
    ingots = Items.FindByID(0x1BF2, 0, beetle.Backpack.Serial, True)
    amount = max(1, 300 - Items.BackpackCount(0x1BF2, 0))
    Items.Move(ingots, Player.Backpack, amount)
    Misc.Pause(625)


def start():
    restock_ingots()
    Mobiles.UseMobile(Mobiles.FindBySerial(0x00065CF4))
    Gumps.WaitForGump(1280077232, 3000)
    make_quest_items()
    turnin()
    Misc.Pause(20000)


while not Player.IsGhost and Player.Weight < 500:
    start()
# turnin()
