
from AutoComplete import *

from lib.util import container_item_count

beetle_serial = 0x00008701
quest_gump = 1280077232
craft_gump = 949095101
npc_serial = 0x00067343
tinker_kit = 0x1bc1
sewing_kit = 0x0F9D

quests = {
    # name, (category, item, amount, item_id)
    'Hute Couture': (8, 86, 10, 0x2306),
    'The Puffy Shirt': (15, 16, 10, 0x1EFD),
    'The King of Clothing': (15, 149, 10, 0x1537),
}


def get_quest():
    quest_name = None
    while quest_name not in quests.keys():
        Mobiles.UseMobile(npc_serial)
        Gumps.WaitForGump(quest_gump, 5000)

        if not Gumps.HasGump(quest_gump):
            return None

        Misc.Pause(625)
        quest_name = Gumps.LastGumpGetLine(
            1).encode('ascii', 'ignore').decode()

    Misc.Pause(625)
    Gumps.SendAction(quest_gump, 4)
    return quest_name


def use_tool():
    if Gumps.CurrentGump() != craft_gump:
        Items.UseItemByID(sewing_kit, -1)
        Gumps.WaitForGump(craft_gump, 5000)
        use_tool()


def action(gump, button):
    Gumps.SendAction(gump, button)
    Gumps.WaitForGump(gump, 5000)


def make_items(category, item, amount):
    use_tool()

    action(craft_gump, category)
    action(craft_gump, item)

    while amount > 1:  # already made 1 above
        use_tool()
        action(craft_gump, 21)  # make last
        amount -= 1


def toggle_quest(id):
    Misc.UseContextMenu(Player.Serial, 'toggle quest item', 5000)
    items = Items.FindAllByID(id, 0, Player.Backpack.Serial, True)
    for item in items:
        Target.WaitForTarget(5000)
        Target.TargetExecute(item)
        Misc.Pause(300)
    Target.Cancel()
    Misc.Pause(625)


def turn_in():
    Mobiles.UseMobile(npc_serial)
    Gumps.WaitForGump(quest_gump, 5000)
    if not Gumps.HasGump(quest_gump):
        return turn_in()
    action(quest_gump, 8)
    Gumps.SendAction(quest_gump, 5)


def restock_ingots():
    beetle = Mobiles.FindBySerial(beetle_serial)
    Items.WaitForContents(beetle.Backpack, 5000)
    ingots = Items.FindByID(0x1BF2, 0, beetle.Backpack.Serial, True)
    amount = max(1, 300 - Items.BackpackCount(0x1BF2, 0))
    Items.Move(ingots, Player.Backpack, amount)
    Misc.Pause(625)


while Player.Weight < 450 and container_item_count(Player.Backpack) < 110:
    quest_name = get_quest()
    category, item, amount, item_id = quests[quest_name]
    make_items(category, item, amount)
    toggle_quest(item_id)
    turn_in()
