
import random

from AutoComplete import *

beetle_serial = Target.PromptTarget('Target your beetle', 90)
npc_serial = 0x0005FB70
quest_gump = 1280077232
craft_gump = 949095101
tinker_kit = 0x1EB8
sewing_kit = 0x0F9D

quests = {
    # name, (category, item, amount, item_id)
    "Necessity's Mother": (15, 23, 10, tinker_kit),
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

    Misc.Pause(200)
    Gumps.SendAction(quest_gump, 4)
    return quest_name


def use_tool():
    if Gumps.CurrentGump() != craft_gump:
        Items.UseItemByID(tinker_kit, -1)
        Gumps.WaitForGump(craft_gump, 5000)
        use_tool()


def action(gump, button):
    Gumps.SendAction(gump, button)
    Gumps.WaitForGump(gump, 5000)


def make_items(category, item, amount, item_id):
    use_tool()

    action(craft_gump, category)
    action(craft_gump, item)

    while amount + 1 > Items.BackpackCount(item_id, 0):
        use_tool()
        action(craft_gump, 21)  # make last


def toggle_quest(id, amount):
    Misc.UseContextMenu(Player.Serial, 'toggle quest item', 5000)
    items = Items.FindAllByID(id, 0, Player.Backpack.Serial, True)
    for item in items[:amount]:
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


def drop_pos():
    player = (Player.Position.X, Player.Position.Y)
    pos = ((-1, -1), (0, -1), (1, -1),
           (-1,  0),          (1,  0),
           (-1,  1), (0,  1), (1,  1))
    return tuple(map(sum, zip(player, random.choice(pos))))


def container_item_count(container):
    for line in Items.GetPropStringList(container):
        if "Contents:" in line:
            return int(line.split('/')[0].replace('Contents: ', ''))


def find_recipes():
    recipes = Items.FindAllByID(0x2831, 0, Player.Backpack.Serial, 3)
    for r in recipes:
        Items.Move(r.Serial, Mobiles.FindBySerial(beetle_serial).Backpack, -1)
        Misc.Pause(625)
    backpacks = Items.FindAllByID(0x0E75, -1, Player.Backpack.Serial, True)
    for b in backpacks:
        Items.MoveOnGround(b, 0, *drop_pos(), Player.Position.Z)
        Misc.Pause(625)


while Player.Weight < Player.MaxWeight - 20 and container_item_count(Player.Backpack) < 110:
    if Items.BackpackCount(0x1BF2, 0) < 100:
        restock_ingots()
        Misc.Pause(625)
    quest_name = get_quest()
    category, item, amount, item_id = quests[quest_name]
    make_items(category, item, amount, item_id)
    toggle_quest(item_id, amount)
    turn_in()

    Misc.Pause(625)
    find_recipes()
