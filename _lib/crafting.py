import re
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from _lib.persistence import load_int, save_int
from _lib.utils import Hue, h, p, stop_script

if TYPE_CHECKING:
    import API


INGOT_GRAPHIC = 0x1BF2
INGOT_HUES = {
    "Iron": 0x0,
    "Dull Copper": 0x973,
    "Shadow Iron": 0x966,
    "Copper": 0x96D,
    "Bronze": 0x972,
    "Gold": 0x8A5,
    "Agapite": 0x979,
    "Verite": 0x89F,
    "Valorite": 0x8AB,
}

PROFESSION_DEFAULTS = {
    "Blacksmith": {
        "tool_type": 0x0FBB,
        "gump_id": 0x38920ABD,
        "make_last_button": 21,
    },
}

CRAFTING_DB = {
    "Blacksmith": {
        "ringmail gloves": {"cat": 1, "idx": 0, "cost": 10},
        "ringmail leggings": {"cat": 1, "idx": 1, "cost": 16},
        "ringmail sleeves": {"cat": 1, "idx": 2, "cost": 14},
        "ringmail tunic": {"cat": 1, "idx": 3, "cost": 18},
        "chainmail coif": {"cat": 1, "idx": 4, "cost": 10},
        "chainmail leggings": {"cat": 1, "idx": 5, "cost": 18},
        "chainmail tunic": {"cat": 1, "idx": 6, "cost": 20},
        "platemail arms": {"cat": 1, "idx": 7, "cost": 18},
        "platemail gloves": {"cat": 1, "idx": 8, "cost": 12},
        "platemail gorget": {"cat": 1, "idx": 9, "cost": 10},
        "platemail legs": {"cat": 1, "idx": 10, "cost": 20},
        "platemail tunic": {"cat": 1, "idx": 11, "cost": 25},
        "platemail female": {"cat": 1, "idx": 12, "cost": 20},
        "dragon barding deed": {"cat": 1, "idx": 13, "cost": 750},
        "ostard barding deed": {"cat": 1, "idx": 14, "cost": 750},
        "platemail mempo": {"cat": 1, "idx": 15, "cost": 18},
        "platemail do": {"cat": 1, "idx": 16, "cost": 28},
        "platemail hiro sode": {"cat": 1, "idx": 17, "cost": 16},
        "platemail suneate": {"cat": 1, "idx": 18, "cost": 20},
        "platemail haidate": {"cat": 1, "idx": 19, "cost": 20},
        "gargish platemail arms": {"cat": 1, "idx": 20, "cost": 18},
        "gargish platemail chest": {"cat": 1, "idx": 21, "cost": 25},
        "gargish platemail leggings": {"cat": 1, "idx": 22, "cost": 20},
        "gargish platemail kilt": {"cat": 1, "idx": 23, "cost": 12},
        "gargish platemail arms (female)": {"cat": 1, "idx": 24, "cost": 18},
        "gargish platemail chest (female)": {"cat": 1, "idx": 25, "cost": 25},
        "gargish platemail leggings (female)": {"cat": 1, "idx": 26, "cost": 20},
        "gargish platemail kilt (female)": {"cat": 1, "idx": 27, "cost": 12},
        "gargish amulet": {"cat": 1, "idx": 28, "cost": 3},
        "britches of warding": {"cat": 1, "idx": 29, "cost": 18},
        "dragon gloves": {"cat": 64, "idx": 0, "cost": 16},
        "dragon helm": {"cat": 64, "idx": 1, "cost": 20},
        "dragon leggings": {"cat": 64, "idx": 2, "cost": 28},
        "dragon sleeves": {"cat": 64, "idx": 3, "cost": 24},
        "dragon breastplate": {"cat": 64, "idx": 4, "cost": 36},
        "crushed glass": {"cat": 64, "idx": 5, "cost": 0},
        "powdered iron": {"cat": 64, "idx": 6, "cost": 20},
        "metal keg": {"cat": 64, "idx": 7, "cost": 25},
        "exodus sacrificial dagger": {"cat": 64, "idx": 8, "cost": 12},
        "gloves of feudal grip": {"cat": 64, "idx": 9, "cost": 18},
        "paladin's pauldron": {"cat": 64, "idx": 10, "cost": 25},
        "feudal collar": {"cat": 64, "idx": 11, "cost": 25},
        "tunic of the inferno": {"cat": 64, "idx": 12, "cost": 25},
        "bardiche": {"cat": 36, "idx": 0, "cost": 18},
        "bladed staff": {"cat": 36, "idx": 1, "cost": 12},
        "double bladed staff": {"cat": 36, "idx": 2, "cost": 16},
        "halberd": {"cat": 36, "idx": 3, "cost": 20},
        "lance": {"cat": 36, "idx": 4, "cost": 20},
        "pike": {"cat": 36, "idx": 5, "cost": 12},
        "short spear": {"cat": 36, "idx": 6, "cost": 6},
        "scythe": {"cat": 36, "idx": 7, "cost": 14},
        "spear": {"cat": 36, "idx": 8, "cost": 12},
        "war fork": {"cat": 36, "idx": 9, "cost": 12},
        "gargish bardiche": {"cat": 36, "idx": 10, "cost": 18},
        "gargish war fork": {"cat": 36, "idx": 11, "cost": 12},
        "gargish scythe": {"cat": 36, "idx": 12, "cost": 14},
        "gargish pike": {"cat": 36, "idx": 13, "cost": 12},
        "gargish lance": {"cat": 36, "idx": 14, "cost": 20},
        "dual pointed spear": {"cat": 36, "idx": 15, "cost": 16},
        "legacy of the crazed mage": {"cat": 36, "idx": 16, "cost": 18},
        "the reptile slayer": {"cat": 36, "idx": 17, "cost": 18},
        "bascinet": {"cat": 8, "idx": 0, "cost": 15},
        "close helmet": {"cat": 8, "idx": 1, "cost": 15},
        "helmet": {"cat": 8, "idx": 2, "cost": 15},
        "norse helm": {"cat": 8, "idx": 3, "cost": 15},
        "plate helm": {"cat": 8, "idx": 4, "cost": 15},
        "chainmail hatsuburi": {"cat": 8, "idx": 5, "cost": 20},
        "platemail hatsuburi": {"cat": 8, "idx": 6, "cost": 20},
        "heavy platemail jingasa": {"cat": 8, "idx": 7, "cost": 20},
        "light platemail jingasa": {"cat": 8, "idx": 8, "cost": 20},
        "small platemail jingasa": {"cat": 8, "idx": 9, "cost": 20},
        "decorative platemail kabuto": {"cat": 8, "idx": 10, "cost": 25},
        "platemail battle kabuto": {"cat": 8, "idx": 11, "cost": 25},
        "standard platemail kabuto": {"cat": 8, "idx": 12, "cost": 25},
        "circlet": {"cat": 8, "idx": 13, "cost": 6},
        "royal circlet": {"cat": 8, "idx": 14, "cost": 6},
        "gemmed circlet": {"cat": 8, "idx": 15, "cost": 6},
        "helm of intuition": {"cat": 8, "idx": 16, "cost": 15},
        "hammer pick": {"cat": 43, "idx": 0, "cost": 16},
        "mace": {"cat": 43, "idx": 1, "cost": 6},
        "maul": {"cat": 43, "idx": 2, "cost": 10},
        "scepter": {"cat": 43, "idx": 3, "cost": 10},
        "war mace": {"cat": 43, "idx": 4, "cost": 14},
        "war hammer": {"cat": 43, "idx": 5, "cost": 16},
        "tessen": {"cat": 43, "idx": 6, "cost": 16},
        "diamond mace": {"cat": 43, "idx": 7, "cost": 20},
        "shard thrasher": {"cat": 43, "idx": 8, "cost": 20},
        "ruby mace": {"cat": 43, "idx": 9, "cost": 20},
        "emerald mace": {"cat": 43, "idx": 10, "cost": 20},
        "sapphire mace": {"cat": 43, "idx": 11, "cost": 20},
        "silver-etched mace": {"cat": 43, "idx": 12, "cost": 20},
        "gargish war hammer": {"cat": 43, "idx": 13, "cost": 16},
        "gargish maul": {"cat": 43, "idx": 14, "cost": 10},
        "gargish tessen": {"cat": 43, "idx": 15, "cost": 16},
        "disc mace": {"cat": 43, "idx": 16, "cost": 20},
        "barbarian's maul": {"cat": 43, "idx": 17, "cost": 20},
        "the demolisher": {"cat": 43, "idx": 18, "cost": 20},
        "buckler": {"cat": 15, "idx": 0, "cost": 10},
        "bronze shield": {"cat": 15, "idx": 1, "cost": 12},
        "heater shield": {"cat": 15, "idx": 2, "cost": 18},
        "metal shield": {"cat": 15, "idx": 3, "cost": 14},
        "metal kite shield": {"cat": 15, "idx": 4, "cost": 16},
        "tear kite shield": {"cat": 15, "idx": 5, "cost": 8},
        "chaos shield": {"cat": 15, "idx": 6, "cost": 25},
        "order shield": {"cat": 15, "idx": 7, "cost": 25},
        "small plate shield": {"cat": 15, "idx": 8, "cost": 12},
        "gargish kite shield": {"cat": 15, "idx": 9, "cost": 16},
        "large plate shield": {"cat": 15, "idx": 10, "cost": 18},
        "medium plate shield": {"cat": 15, "idx": 11, "cost": 14},
        "gargish chaos shield": {"cat": 15, "idx": 12, "cost": 25},
        "gargish order shield": {"cat": 15, "idx": 13, "cost": 25},
        "aethena": {"cat": 15, "idx": 14, "cost": 25},
        "enigmatic shield": {"cat": 15, "idx": 15, "cost": 25},
        "cannonball": {"cat": 50, "idx": 0, "cost": 12},
        "grapeshot": {"cat": 50, "idx": 1, "cost": 12},
        "culverin": {"cat": 50, "idx": 2, "cost": 12},
        "carronade": {"cat": 50, "idx": 3, "cost": 12},
        "bone harvester": {"cat": 22, "idx": 0, "cost": 10},
        "broadsword": {"cat": 22, "idx": 1, "cost": 10},
        "crescent blade": {"cat": 22, "idx": 2, "cost": 14},
        "cutlass": {"cat": 22, "idx": 3, "cost": 8},
        "dagger": {"cat": 22, "idx": 4, "cost": 3},
        "katana": {"cat": 22, "idx": 5, "cost": 8},
        "kryss": {"cat": 22, "idx": 6, "cost": 8},
        "longsword": {"cat": 22, "idx": 7, "cost": 12},
        "scimitar": {"cat": 22, "idx": 8, "cost": 10},
        "viking sword": {"cat": 22, "idx": 9, "cost": 14},
        "no-dachi": {"cat": 22, "idx": 10, "cost": 18},
        "wakizashi": {"cat": 22, "idx": 11, "cost": 8},
        "lajatang": {"cat": 22, "idx": 12, "cost": 25},
        "daisho": {"cat": 22, "idx": 13, "cost": 15},
        "tekagi": {"cat": 22, "idx": 14, "cost": 12},
        "shuriken": {"cat": 22, "idx": 15, "cost": 5},
        "kama": {"cat": 22, "idx": 16, "cost": 14},
        "sai": {"cat": 22, "idx": 17, "cost": 12},
        "radiant scimitar": {"cat": 22, "idx": 18, "cost": 15},
        "war cleaver": {"cat": 22, "idx": 19, "cost": 18},
        "elven spellblade": {"cat": 22, "idx": 20, "cost": 14},
        "assassin spike": {"cat": 22, "idx": 21, "cost": 9},
        "leafblade": {"cat": 22, "idx": 22, "cost": 12},
        "rune blade": {"cat": 22, "idx": 23, "cost": 15},
        "elven machete": {"cat": 22, "idx": 24, "cost": 14},
        "rune carving knife": {"cat": 22, "idx": 25, "cost": 9},
        "cold forged blade": {"cat": 22, "idx": 26, "cost": 18},
        "overseer sundered blade": {"cat": 22, "idx": 27, "cost": 15},
        "luminous rune blade": {"cat": 22, "idx": 28, "cost": 15},
        "true spellblade": {"cat": 22, "idx": 29, "cost": 14},
        "icy spellblade": {"cat": 22, "idx": 30, "cost": 14},
        "fiery spellblade": {"cat": 22, "idx": 31, "cost": 14},
        "spellblade of defense": {"cat": 22, "idx": 32, "cost": 18},
        "true assassin spike": {"cat": 22, "idx": 33, "cost": 9},
        "charged assassin spike": {"cat": 22, "idx": 34, "cost": 9},
        "magekiller": {"cat": 22, "idx": 35, "cost": 9},
        "assassin spike (gargish)": {"cat": 22, "idx": 36, "cost": 9},
        "wounding assassin spike": {"cat": 22, "idx": 37, "cost": 9},
        "true leafblade": {"cat": 22, "idx": 38, "cost": 12},
        "luckblade": {"cat": 22, "idx": 39, "cost": 12},
        "magekiller (gargish)": {"cat": 22, "idx": 40, "cost": 12},
        "leafblade (gargish)": {"cat": 22, "idx": 41, "cost": 12},
        "leafblade of ease": {"cat": 22, "idx": 42, "cost": 12},
        "knight's war cleaver": {"cat": 22, "idx": 43, "cost": 18},
        "butcher's war cleaver": {"cat": 22, "idx": 44, "cost": 18},
        "serrated war cleaver": {"cat": 22, "idx": 45, "cost": 18},
        "true war cleaver": {"cat": 22, "idx": 46, "cost": 18},
        "adventurer's machete": {"cat": 22, "idx": 47, "cost": 14},
        "orcish machete": {"cat": 22, "idx": 48, "cost": 14},
        "machete of defense": {"cat": 22, "idx": 49, "cost": 14},
        "diseased machete": {"cat": 22, "idx": 50, "cost": 14},
        "runesabre": {"cat": 22, "idx": 51, "cost": 15},
        "mage's rune blade": {"cat": 22, "idx": 52, "cost": 15},
        "rune blade of knowledge": {"cat": 22, "idx": 53, "cost": 15},
        "corrupted rune blade": {"cat": 22, "idx": 54, "cost": 15},
        "true radiant scimitar": {"cat": 22, "idx": 55, "cost": 15},
        "darkglow scimitar": {"cat": 22, "idx": 56, "cost": 15},
        "icy scimitar": {"cat": 22, "idx": 57, "cost": 15},
        "twinkling scimitar": {"cat": 22, "idx": 58, "cost": 15},
        "bone machete": {"cat": 22, "idx": 59, "cost": 20},
        "gargish katana": {"cat": 22, "idx": 60, "cost": 8},
        "gargish kryss": {"cat": 22, "idx": 61, "cost": 8},
        "gargish bone harvester": {"cat": 22, "idx": 62, "cost": 10},
        "gargish tekagi": {"cat": 22, "idx": 63, "cost": 12},
        "gargish daisho": {"cat": 22, "idx": 64, "cost": 15},
        "dread sword": {"cat": 22, "idx": 65, "cost": 14},
        "gargish talwar": {"cat": 22, "idx": 66, "cost": 18},
        "gargish dagger": {"cat": 22, "idx": 67, "cost": 3},
        "bloodblade": {"cat": 22, "idx": 68, "cost": 8},
        "shortblade": {"cat": 22, "idx": 69, "cost": 12},
        "basilisk's tooth": {"cat": 22, "idx": 70, "cost": 12},
        "death's kiss": {"cat": 22, "idx": 71, "cost": 12},
        "insane blade": {"cat": 22, "idx": 72, "cost": 12},
        "boomerang": {"cat": 57, "idx": 0, "cost": 5},
        "cyclone": {"cat": 57, "idx": 1, "cost": 9},
        "soul": {"cat": 57, "idx": 2, "cost": 9},
        "glaive": {"cat": 57, "idx": 3, "cost": 9},
        "axe": {"cat": 29, "idx": 0, "cost": 14},
        "battle axe": {"cat": 29, "idx": 1, "cost": 14},
        "double axe": {"cat": 29, "idx": 2, "cost": 12},
        "executioner's axe": {"cat": 29, "idx": 3, "cost": 14},
        "large battle axe": {"cat": 29, "idx": 4, "cost": 12},
        "two handed axe": {"cat": 29, "idx": 5, "cost": 16},
        "war axe": {"cat": 29, "idx": 6, "cost": 16},
        "ornate axe": {"cat": 29, "idx": 7, "cost": 18},
        "guardian axe": {"cat": 29, "idx": 8, "cost": 15},
        "singing axe": {"cat": 29, "idx": 9, "cost": 15},
        "thundering axe": {"cat": 29, "idx": 10, "cost": 15},
        "heavy ornate axe": {"cat": 29, "idx": 11, "cost": 15},
        "gargish battle axe": {"cat": 29, "idx": 12, "cost": 14},
        "gargish axe": {"cat": 29, "idx": 13, "cost": 14},
        "dual short axes": {"cat": 29, "idx": 14, "cost": 24},
        "axe of the gods": {"cat": 29, "idx": 15, "cost": 18},
    },
}

RESOURCE_BOX_BUTTONS = {
    "Iron": 100,
    "Dull Copper": 101,
    "Shadow Iron": 102,
    "Copper": 103,
    "Bronze": 104,
    "Gold": 105,
    "Agapite": 106,
    "Verite": 107,
    "Valorite": 108,
}

TONGS_TYPE = 0x0FBB
TINKER_TOOLS_TYPE = 0x1EB8
SALVAGE_BAG_GRAPHIC = 0x0E76
BLACKSMITH_TOOL_GROUND = 0x9A81
TOOL_GROUND_RANGE = 3

RESOURCE_BOX_GUMP = 0x23D0F169
TINKER_GUMP = 0x38920ADB
SMALL_BOD_GUMP = 0x5AFBD742
LARGE_BOD_GUMP = 0xA125B54A
BOD_ADD_ITEMS_BUTTON = 4

MATERIAL_MENU_BUTTON = 7
MATERIAL_BUTTONS = {
    "Iron": 6,
    "Dull Copper": 13,
    "Shadow Iron": 20,
    "Copper": 27,
    "Bronze": 34,
    "Gold": 41,
    "Agapite": 48,
    "Verite": 55,
    "Valorite": 62,
}

TOOL_BREAK_MESSAGE = "You have worn out your tool!"
NOT_ENOUGH_MATERIALS = "You do not have sufficient"


class ToolManager:
    def __init__(self):
        self.tinker_tools: List[int] = []
        self.tongs: Optional[int] = None
        self.salvage_bag: Optional[int] = None
        self._scan_tools()

    def _scan_tools(self) -> None:
        self.tinker_tools = []
        self.tongs = None
        self.salvage_bag = None

        self._scan_container(API.Backpack)

    def _scan_container(self, container_serial: int) -> None:
        items = API.ItemsInContainer(container_serial, recursive=True)
        if not items:
            return

        for item in items:
            if item.Graphic == TINKER_TOOLS_TYPE:
                self.tinker_tools.append(item.Serial)
            elif item.Graphic == TONGS_TYPE:
                self.tongs = item.Serial
            elif item.Graphic == SALVAGE_BAG_GRAPHIC:
                props = API.ItemNameAndProps(item.Serial, wait=True, timeout=1)
                if props and "Salvage Bag" in props.split("\n")[0]:
                    self.salvage_bag = item.Serial

    def find_ground_tool(self) -> Optional[int]:
        item = API.FindType(BLACKSMITH_TOOL_GROUND, range=TOOL_GROUND_RANGE)
        if item and item.Distance <= TOOL_GROUND_RANGE:
            return item.Serial
        return None

    def has_blacksmith_tool(self) -> bool:
        if self.tongs and API.FindItem(self.tongs):
            return True
        self._scan_tools()
        return self.tongs is not None

    def get_blacksmith_tool(self) -> Optional[int]:
        ground_tool = self.find_ground_tool()
        if ground_tool:
            return ground_tool
        if not self.has_blacksmith_tool():
            return None
        return self.tongs

    def has_tinker_tools(self, min_count: int = 2) -> bool:
        valid_tools = []
        for serial in self.tinker_tools:
            if API.FindItem(serial):
                valid_tools.append(serial)

        self.tinker_tools = valid_tools

        if len(self.tinker_tools) >= min_count:
            return True

        self._scan_tools()
        return len(self.tinker_tools) >= min_count

    def get_tinker_tool(self) -> Optional[int]:
        if not self.has_tinker_tools(min_count=1):
            return None
        return self.tinker_tools[0] if self.tinker_tools else None

    def ensure_tinker_tools(self) -> bool:
        if self.has_tinker_tools(min_count=2):
            return True

        tool = self.get_tinker_tool()
        if not tool:
            return False

        API.UseObject(tool)
        API.Pause(1.0)

        self._scan_tools()
        return self.has_tinker_tools(min_count=2)

    def handle_tool_break(self) -> bool:
        self._scan_tools()

        if not self.has_blacksmith_tool():
            if not self.craft_tongs():
                return False

        return True

    def craft_tongs(self) -> bool:
        if not self.has_tinker_tools(min_count=1):
            return False

        tool = self.get_tinker_tool()
        if not tool:
            return False

        API.UseObject(tool)
        API.WaitForGump(TINKER_GUMP, delay=2.0)

        if not API.HasGump(TINKER_GUMP):
            return False

        API.ReplyGump(1, TINKER_GUMP)
        API.WaitForGump(TINKER_GUMP, delay=1.0)
        API.ReplyGump(10, TINKER_GUMP)
        API.WaitForGump(TINKER_GUMP, delay=1.0)

        API.Pause(1.0)

        self._scan_tools()
        return self.has_blacksmith_tool()

    def get_salvage_bag(self) -> Optional[int]:
        if not self.salvage_bag:
            self._scan_tools()
        return self.salvage_bag

    def salvage_items(self, items: List[int]) -> bool:
        salvage_bag = self.get_salvage_bag()
        if not salvage_bag:
            p("WARNING: No salvage bag found!", Hue.Orange)
            return False

        for item_serial in items:
            API.MoveItem(item_serial, salvage_bag)
            API.Pause(0.5)

        API.ContextMenu(salvage_bag, 2)
        API.Pause(1.0)

        return True


class ResourceStorage:
    RESOURCE_BOX_GUMP = 0x23D0F169
    RESOURCE_BOX_SERIAL_KEY = "ResourceBoxSerial"

    def __init__(self):
        self.serial: Optional[int] = None
        self._load_serial()

    def _load_serial(self) -> None:
        serial = load_int(self.RESOURCE_BOX_SERIAL_KEY, default=0)
        if serial:
            item = API.FindItem(serial)
            if item and item.Distance <= 2:
                self.serial = serial

    def _save_serial(self) -> None:
        if self.serial:
            save_int(self.RESOURCE_BOX_SERIAL_KEY, self.serial)

    def find_resource_box(self) -> bool:
        if self.serial:
            item = API.FindItem(self.serial)
            if item and item.Distance <= 2:
                return True

        p("Please target your resource box...", Hue.Cyan)
        target = API.RequestTarget(timeout=10.0)

        if not target:
            p("No target selected.", Hue.Red)
            return False

        item = API.FindItem(target)
        if not item:
            p("Invalid target.", Hue.Red)
            return False

        if item.Distance > 2:
            p("Resource box too far away (>2 tiles).", Hue.Red)
            return False

        self.serial = target
        self._save_serial()
        p(f"Resource box saved: {hex(self.serial)}", Hue.Green)
        return True

    def withdraw_material(self, material: str, amount: int) -> bool:
        if not self.find_resource_box():
            return False

        button = RESOURCE_BOX_BUTTONS.get(material)
        if not button:
            p(f"ERROR: Unknown material: {material}", Hue.Red)
            return False

        if not self.serial:
            p("ERROR: No resource box serial available!", Hue.Red)
            return False

        API.UseObject(self.serial)
        API.WaitForGump(self.RESOURCE_BOX_GUMP, delay=2.0)

        if not API.HasGump(self.RESOURCE_BOX_GUMP):
            p("ERROR: Resource box gump did not open!", Hue.Red)
            return False

        p(f"Withdrawing {amount} {material} ingots...", Hue.Cyan)

        ingots_in_pack = self._count_ingots(material)
        attempts = 0
        max_attempts = amount

        while ingots_in_pack < amount and attempts < max_attempts:
            API.ReplyGump(button, self.RESOURCE_BOX_GUMP)
            API.Pause(0.5)

            new_count = self._count_ingots(material)
            if new_count == ingots_in_pack:
                p(f"WARNING: No more {material} ingots in resource box!", Hue.Red)
                return False

            ingots_in_pack = new_count
            attempts += 1

        if ingots_in_pack < amount:
            p(f"ERROR: Could only withdraw {ingots_in_pack}/{amount} ingots!", Hue.Red)
            return False

        API.CloseGump(self.RESOURCE_BOX_GUMP)
        p(f"Successfully withdrew {ingots_in_pack} {material} ingots.", Hue.Green)
        return True

    def _count_ingots(self, material: str) -> int:
        hue = INGOT_HUES.get(material, 0)
        total = 0
        items = API.FindTypeAll(INGOT_GRAPHIC, API.Backpack, hue=hue) or []
        for item in items:
            total += item.Amount
        return total


class CraftingEngine:
    def __init__(self, tool_manager: ToolManager, profession: str = "Blacksmith"):
        self.tool_manager = tool_manager
        self.profession = profession
        self._crafted_items: List[int] = []
        defaults = PROFESSION_DEFAULTS.get(
            profession, PROFESSION_DEFAULTS["Blacksmith"]
        )
        self.gump_id = defaults["gump_id"]
        self.make_last_button = defaults["make_last_button"]

    def open_gump(self) -> bool:
        tool = self.tool_manager.get_blacksmith_tool()
        if not tool:
            p("ERROR: No blacksmith tool available!", Hue.Red)
            return False

        if API.HasGump(self.gump_id):
            return True

        API.UseObject(tool)
        return API.WaitForGump(self.gump_id)

    def get_buttons(self, recipe: dict) -> "tuple[int, int]":
        cat = recipe["cat"]
        item_btn = 2 + (recipe["idx"] * 7)
        return (cat, item_btn)

    def craft_item(self, item_name: str, profession: str) -> Optional[int]:
        prof_db = CRAFTING_DB.get(profession, {})
        recipe = prof_db.get(item_name.lower())
        if not recipe:
            p(f"ERROR: No recipe for {item_name}", Hue.Red)
            return None

        if not self.open_gump():
            return None

        cat_btn, item_btn = self.get_buttons(recipe)
        API.ReplyGump(cat_btn, self.gump_id)
        API.WaitForGump(self.gump_id, delay=1.0)

        API.ReplyGump(item_btn, self.gump_id)
        API.WaitForGump(self.gump_id, delay=2.0)

        API.Pause(1.0)

        if API.InJournal(TOOL_BREAK_MESSAGE, True):
            if not self.tool_manager.handle_tool_break():
                return None
            return self.craft_item(item_name, profession)

        return None

    def craft_with_quality_check(
        self,
        item_name: str,
        profession: str,
        target_quality: str,
        needed: int,
        material: str = "Iron",
    ) -> Tuple[int, int]:
        exceptional_count = 0
        normal_count = 0
        max_attempts = needed * 3
        attempts = 0

        prof_db = CRAFTING_DB.get(profession, {})
        recipe = prof_db.get(item_name.lower())
        if not recipe:
            p(f"ERROR: No recipe for {item_name}", Hue.Red)
            return (0, 0)

        cat_btn, item_btn = self.get_buttons(recipe)
        material_btn = MATERIAL_BUTTONS.get(material, 6)

        while exceptional_count < needed and attempts < max_attempts:
            if not self.open_gump():
                break

            if attempts == 0:
                API.ReplyGump(MATERIAL_MENU_BUTTON, self.gump_id)
                API.WaitForGump(self.gump_id)
                API.ReplyGump(material_btn, self.gump_id)
                API.WaitForGump(self.gump_id)

                API.ReplyGump(cat_btn, self.gump_id)
                API.WaitForGump(self.gump_id)
                API.ReplyGump(item_btn, self.gump_id)
            else:
                API.ReplyGump(self.make_last_button, self.gump_id)

            API.WaitForGump(self.gump_id)
            API.Pause(0.3)

            if API.InJournal(TOOL_BREAK_MESSAGE, True):
                if not self.tool_manager.handle_tool_break():
                    break
                continue

            if API.InJournal(NOT_ENOUGH_MATERIALS, True):
                p("ERROR: Out of materials!", Hue.Red)
                break

            attempts += 1

            if target_quality == "Exceptional":
                exceptional_count += 1
            else:
                normal_count += 1

        return (exceptional_count, normal_count)


class BODCrafter:
    def __init__(self, profession: str = "Blacksmith"):
        self.profession = profession
        self.tool_manager = ToolManager()
        self.resource_storage = ResourceStorage()
        self.crafting_engine = CraftingEngine(self.tool_manager, profession)
        self.max_items = 90
        self.max_weight = API.Player.WeightMax - 60

    def preflight_check(self) -> bool:
        if API.Player.Weight > self.max_weight:
            p(
                f"ERROR: Weight too high ({API.Player.Weight} > {self.max_weight})",
                Hue.Red,
            )
            return False

        item_count = API.Contents(API.Backpack)
        if item_count > self.max_items:
            p(f"ERROR: Too many items ({item_count} > {self.max_items})", Hue.Red)
            return False

        if not self.tool_manager.has_blacksmith_tool():
            p("ERROR: No blacksmith tool found!", Hue.Red)
            return False

        if not self.tool_manager.has_tinker_tools(min_count=2):
            if not self.tool_manager.ensure_tinker_tools():
                return False

        if not self.resource_storage.find_resource_box():
            p("ERROR: Resource box not accessible!", Hue.Red)
            return False

        return True

    def process_bod(self, bod) -> bool:
        p(f"Processing: {bod}", Hue.Green)

        remaining = bod.remaining()
        if remaining <= 0:
            p("BOD already complete!", Hue.Yellow)
            return True

        prof_db = CRAFTING_DB.get(bod.profession, {})
        recipe = prof_db.get(bod.item_name.lower())
        if not recipe:
            p(f"ERROR: No crafting data for {bod.item_name}", Hue.Red)
            return False

        materials_needed = remaining * recipe["cost"]

        if not self.resource_storage.withdraw_material(bod.material, materials_needed):
            return False

        target_quality = "Exceptional" if bod.exceptional else "Normal"
        exceptional_count, normal_count = self.crafting_engine.craft_with_quality_check(
            bod.item_name, bod.profession, target_quality, remaining, bod.material
        )

        crafted = exceptional_count if bod.exceptional else normal_count
        if crafted >= remaining:
            p(f"Successfully crafted {crafted}/{remaining} items!", Hue.Green)
            if self._add_items_to_bod(bod):
                p("Items added to BOD.", Hue.Green)
            else:
                p("ERROR: Failed to add items to BOD!", Hue.Red)
        else:
            p(f"WARNING: Only crafted {crafted}/{remaining} items", Hue.Orange)

        if bod.exceptional and normal_count > 0:
            p(f"Salvaging {normal_count} normal items...", Hue.Cyan)

        return crafted >= remaining

    def _add_items_to_bod(self, bod) -> bool:
        p("Adding items to BOD...", Hue.Cyan)

        gump = LARGE_BOD_GUMP if bod.is_large else SMALL_BOD_GUMP

        API.UseObject(bod.serial)
        if not API.WaitForGump(gump):
            p("ERROR: BOD gump didn't open!", Hue.Red)
            return False

        API.ReplyGump(BOD_ADD_ITEMS_BUTTON, gump)

        if API.WaitForTarget(timeout=2.0):
            API.Target(API.Backpack)  # pyright:ignore
            API.Pause(0.5)

        return True

    def process_bods(self, bods: List) -> None:
        if not bods:
            p("No BODs to process!", Hue.Orange)
            return

        if not self.preflight_check():
            stop_script("Pre-flight check failed")
            return

        material_groups: Dict[str, List] = {}
        for bod in bods:
            if bod.is_complete():
                continue

            material = bod.material
            if material not in material_groups:
                material_groups[material] = []
            material_groups[material].append(bod)

        materials = sorted(material_groups.keys(), key=lambda m: (m != "Iron", m))

        for material in materials:
            p(f"\n=== Processing {material} BODs ===", Hue.Cyan)

            for bod in material_groups[material]:
                if not self.process_bod(bod):
                    p(f"Failed to process BOD: {bod.item_name}", Hue.Red)
                    continue

        p("\n=== BOD processing complete ===", Hue.Green)


def move_resource_box(source=None, destination=None):
    GUMP_ID = 0x23D0F169
    ITEM_RE = re.compile(r"^([A-Za-z]+)$", re.MULTILINE)
    QTY_RE = re.compile(r"^(\d+)$", re.MULTILINE)
    BUTTON_RE = re.compile(
        r"^button\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)$", re.MULTILINE
    )

    def parse_gump_packet_text(text):
        item_names = ITEM_RE.findall(text)
        quantities = QTY_RE.findall(text)
        button_ids = [int(b) for b in BUTTON_RE.findall(text) if int(b) >= 100]

        items = list(zip(item_names, [int(q) for q in quantities]))
        paired = list(zip(items, button_ids))

        return [btn for (_, qty), btn in paired if qty > 0]

    if not source:
        h("target source resource box")
        tar = API.RequestTarget(30)
        if not tar:
            return
        source = API.FindItem(tar)

    if not destination:
        h("target destination resource box")
        tar = API.RequestTarget(30)
        if not tar:
            return
        destination = API.FindItem(tar)

    API.UseObject(destination)
    API.WaitForGump(GUMP_ID)
    API.ReplyGump(1, GUMP_ID)
    API.WaitForTarget()

    API.UseObject(source)
    API.WaitForGump(GUMP_ID)

    while API.HasGump(GUMP_ID):
        text = API.GetGump(GUMP_ID).PacketGumpText
        buttons = parse_gump_packet_text(text)

        if not buttons:
            return

        btn = buttons.pop()

        if API.Player.WeightMax - API.Player.Weight < 50:
            API.Target(API.Backpack)  # pyright:ignore
            API.WaitForTarget()

        API.ReplyGump(btn, GUMP_ID)
        API.WaitForGump(GUMP_ID)
