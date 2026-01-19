import random
import re

import API
from _lib.items import move_item_robust
from _lib.utils import count_items, p

DEFAULT_PAUSE = 0.65
QUEST_NAME_REGEX = re.compile(r"Quest Offer (.+) Description", re.I)

p("Target Beetle!")
beetle_serial = API.RequestTarget()


npc_serial = 0x31899
quest_gump = 0x4C4C6DB0
craft_gump = 0x38920ABD
tinker_kit = 0x1EB8


quests = {
    # name, (category, item, amount, item_id)
    "Necessity's Mother": (15, 23, 10, tinker_kit),
}


def get_quest():
    attempts = 35
    while attempts > 0:
        attempts -= 1
        gump_contents = None

        API.UseObject(npc_serial)
        API.WaitForGump(quest_gump)
        if not API.HasGump(quest_gump):
            return None

        gump_contents = API.GetGumpContents(quest_gump)
        while not gump_contents:
            API.Pause(0.3)

        match = QUEST_NAME_REGEX.match(gump_contents)
        if not match:
            attempts -= 1
            continue

        if match.group(1) in quests.keys():
            quest_name = match.group(1)
            API.ReplyGump(4, quest_gump)
            return quest_name

        API.CloseGump(quest_gump)
        API.Pause(DEFAULT_PAUSE * 2)

    p("unable to get quest, exceeded number of attempts", 36)
    API.Stop()


def use_tool():
    if not API.HasGump(craft_gump):
        API.UseType(tinker_kit, 0, API.Player.Backpack)
        API.WaitForGump(craft_gump, 5)
        use_tool()


def action(gump, button):
    API.ReplyGump(button, gump)
    API.WaitForGump(gump)


def make_items(category, item, amount, item_id):
    use_tool()

    action(craft_gump, category)
    action(craft_gump, item)

    while amount + 1 > count_items(item_id, API.Backpack):
        use_tool()
        action(craft_gump, 21)  # make last


def toggle_quest(id, amount):
    API.ContextMenu(API.Player, 7)
    items = API.FindTypeAll(id, API.Backpack, hue=0)

    count = 0
    while count < amount:
        API.WaitForTarget(timeout=3)
        API.Target(items[count])  # pyright:ignore
        while not API.InJournal("You set the item to Quest Item status", True):
            API.Pause(0.05)
        count += 1

    API.CancelTarget()
    API.Pause(0.6)


def turn_in():
    API.UseObject(npc_serial)
    API.WaitForGump(quest_gump)
    if not API.HasGump(quest_gump):
        API.Pause(DEFAULT_PAUSE)
        return turn_in()
    action(quest_gump, 8)
    API.ReplyGump(5, quest_gump)


def restock_ingots():
    if not beetle_serial:
        return

    beetle = API.FindMobile(beetle_serial)
    if not beetle or not getattr(beetle, "Backpack", None):
        return

    API.UseObject(beetle.Backpack)
    API.Pause(1.0)

    ingots = API.FindType(0x1BF2, beetle.Backpack, hue=0)
    if not ingots:
        return

    amount = max(1, 300 - count_items(0x1BF2, API.Backpack))
    move_item_robust(ingots, API.Backpack, amount)


def drop_pos():
    player = (API.Player.X, API.Player.Y)
    pos = ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1))
    return tuple(map(sum, zip(player, random.choice(pos))))


def find_recipes():
    if not beetle_serial:
        return

    for backpack in API.FindTypeAll(0x0E75, API.Backpack):
        if backpack.Serial == API.Backpack:
            continue

        API.UseObject(backpack)
        API.Pause(DEFAULT_PAUSE)
        for recipe in API.FindTypeAll(0x2831, backpack):
            move_item_robust(recipe, beetle_serial, 1)

        pos = drop_pos()
        API.MoveItem(backpack, 4294967295, 1, pos[0], pos[1])
        API.Pause(DEFAULT_PAUSE)


while (
    API.Player.Weight < API.Player.WeightMax - 20
    and API.Contents(API.Backpack) < 110
    and not API.StopRequested
):
    if not API.FindType(0x1BF2, API.Backpack, hue=0, minamount=100):
        restock_ingots()
        API.Pause(DEFAULT_PAUSE)

    quest_name = get_quest()
    if not quest_name:
        API.Pause(DEFAULT_PAUSE)
        continue

    category, item, amount, item_id = quests[quest_name]
    # make_items(category, item, amount, item_id)
    make_items(*quests[quest_name])
    toggle_quest(item_id, amount)
    turn_in()

    API.Pause(DEFAULT_PAUSE)
    find_recipes()
