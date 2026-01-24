import random
import re
from typing import Optional

import API
from _lib import persistence
from _lib.items import move_item_robust
from _lib.utils import count_items, p


class HeartwoodTinker:
    QUEST_GUMP = 0x4C4C6DB0
    CRAFT_GUMP = 0x38920ABD
    TINKER_KIT = 0x1EB8
    INGOT_GRAPHIC = 0x1BF2
    BACKPACK_GRAPHIC = 0x0E75
    RECIPE_GRAPHIC = 0x2831
    DEFAULT_PAUSE = 0.65

    QUEST_NAME_REGEX = re.compile(r"Quest Offer (.+) Description", re.I)

    QUESTS = {
        "Necessity's Mother": (15, 23, 10, TINKER_KIT),
    }

    def __init__(self):
        self.beetle_serial = None
        self.npc_serial = None

    def main(self):
        self._setup_serials()
        while not API.StopRequested:
            self._run_cycle()

    def _setup_serials(self):
        self.beetle_serial = persistence.setup_target(
            "HeartwoodTinker:beetle_serial", "Target Beetle!"
        )
        self.npc_serial = persistence.setup_target(
            "HeartwoodTinker:npc_serial", "Target Tinker NPC!"
        )

    def _run_cycle(self):
        if API.Player.Weight >= API.Player.WeightMax - 20:
            p("weight limit reached")
            API.Stop()
            return

        if API.Contents(API.Backpack) > 110:
            p("backpack full")
            API.Stop()
            return

        if not API.FindType(self.INGOT_GRAPHIC, API.Backpack, hue=0, minamount=100):
            if not self._restock_ingots():
                p("not enough ingots and can't restock")
                API.Stop()
                return
            API.Pause(self.DEFAULT_PAUSE)

        quest_name = self._get_quest()
        if not quest_name:
            API.Pause(self.DEFAULT_PAUSE)
            return

        category, item, amount, item_id = self.QUESTS[quest_name]
        self._make_items(category, item, amount, item_id)
        self._toggle_quest(item_id, amount)
        self._turn_in()

        API.Pause(self.DEFAULT_PAUSE)
        self._find_recipes()

    def _get_quest(self) -> Optional[str]:
        attempts = 35
        while attempts > 0:
            attempts -= 1
            gump_contents = None

            API.UseObject(self.npc_serial)  # type:ignore
            API.WaitForGump(self.QUEST_GUMP)
            if not API.HasGump(self.QUEST_GUMP):
                return None

            gump_contents = API.GetGumpContents(self.QUEST_GUMP)
            while not gump_contents:
                API.Pause(0.3)

            match = self.QUEST_NAME_REGEX.match(gump_contents)
            if not match:
                continue

            if match.group(1) in self.QUESTS:
                quest_name = match.group(1)
                API.ReplyGump(4, self.QUEST_GUMP)
                return quest_name

            API.CloseGump(self.QUEST_GUMP)
            API.Pause(self.DEFAULT_PAUSE)

        p("unable to get quest, exceeded number of attempts", 36)
        API.Stop()

    def _use_tool(self, attempts: int = 20) -> None:
        if API.HasGump(self.CRAFT_GUMP):
            return

        if not API.FindType(self.TINKER_KIT, API.Backpack):
            p("no tinker kits in backpack")
            return

        if attempts <= 0:
            p("failed to open tinker gump")
            return

        API.UseType(self.TINKER_KIT, 0, API.Player.Backpack)
        API.WaitForGump(self.CRAFT_GUMP)
        self._use_tool(attempts - 1)

    def _action(self, gump: int, button: int) -> None:
        API.ReplyGump(button, gump)
        API.WaitForGump(gump)

    def _make_items(self, category: int, item: int, amount: int, item_id: int) -> None:
        self._use_tool()

        self._action(self.CRAFT_GUMP, category)
        self._action(self.CRAFT_GUMP, item)

        while amount + 1 > count_items(item_id, API.Backpack):
            self._use_tool()
            self._action(self.CRAFT_GUMP, 21)  # make last

    def _toggle_quest(self, item_id: int, amount: int) -> None:
        API.ContextMenu(API.Player, 7)
        items = API.FindTypeAll(item_id, API.Backpack, hue=0)

        count = 0
        while count < amount:
            API.WaitForTarget(timeout=3)
            API.Target(items[count])  # pyright:ignore
            while not API.InJournal("You set the item to Quest Item status", True):
                API.Pause(0.05)
            count += 1

        API.CancelTarget()
        API.Pause(self.DEFAULT_PAUSE)

    def _turn_in(self) -> None:
        API.UseObject(self.npc_serial)  # type:ignore
        API.WaitForGump(self.QUEST_GUMP)
        if not API.HasGump(self.QUEST_GUMP):
            API.Pause(self.DEFAULT_PAUSE)
            return self._turn_in()
        self._action(self.QUEST_GUMP, 8)
        API.ReplyGump(5, self.QUEST_GUMP)

    def _restock_ingots(self) -> bool:
        beetle = API.FindMobile(self.beetle_serial)  # type:ignore
        if not beetle or not getattr(beetle, "Backpack", None):
            return False

        API.UseObject(beetle.Backpack)
        API.Pause(1.0)

        ingots = API.FindType(self.INGOT_GRAPHIC, beetle.Backpack, hue=0)
        if not ingots:
            return False

        amount = max(1, 300 - count_items(self.INGOT_GRAPHIC, API.Backpack))
        move_item_robust(ingots, API.Backpack, amount)

        return True

    def _find_recipes(self) -> None:
        for backpack in API.FindTypeAll(self.BACKPACK_GRAPHIC, API.Backpack):
            if backpack.Serial == API.Backpack:
                continue

            API.UseObject(backpack)
            API.Pause(self.DEFAULT_PAUSE)
            for recipe in API.FindTypeAll(self.RECIPE_GRAPHIC, backpack):
                move_item_robust(recipe, self.beetle_serial, 1)

            pos = self._drop_pos()
            API.MoveItem(backpack, 4294967295, 1, pos[0], pos[1])
            API.Pause(self.DEFAULT_PAUSE)

    def _drop_pos(self) -> "tuple[int, int]":
        player_x, player_y = API.Player.X, API.Player.Y
        offsets = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
        dx, dy = random.choice(offsets)
        return (player_x + dx, player_y + dy)


hwt = HeartwoodTinker()
hwt.main()
