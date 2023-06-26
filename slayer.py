
import re
from collections import defaultdict, namedtuple

from AutoComplete import *

from lib.util import Hue, search_subcontainers

SkillValue = namedtuple("Skill", ["Name", "Value"])


class Slayer:
    gump_id = 835374663
    re = re.compile(r"(.+?)( slayer)?$", re.IGNORECASE)

    ids = [
        1060457,  # air elemental
        1060458,  # arachnid
        1060459,  # blood elemental
        1060460,  # demon
        1060461,  # demon (?)
        1060462,  # dragon
        1060463,  # earth elemental
        1060464,  # elemental
        1060465,  # fire elemental
        1060466,  # gargoyle
        1060467,  # lizardman
        1060468,  # ogre
        1060469,  # ophidian
        1060470,  # orc
        1060471,  # poison elemental
        1060472,  # repond
        1060473,  # reptile
        1060474,  # scorpion
        1060475,  # snake
        1060476,  # snow elemental
        1060477,  # spider
        1060478,  # terathan
        1060479,  # undead
        1060480,  # troll
        1060481,  # water elemental
        1070855,  # fey
        1071451,  # silver
    ]

    def __init__(self) -> None:
        self.active = 0
        self.slayers = self.find_weapons()
        self.gump()

    def get_slayer_prop(self, item):
        if not any(prop.Number == 0x103134 for prop in item.Properties):
            return None  # not a swordsmanship weapon
        slayer_prop = next(
            (prop.ToString() for prop in item.Properties if prop.Number in self.ids), None)
        if not slayer_prop:
            return None
        return re.sub(self.re, r"\1", slayer_prop).lower()

    def get_equipped_slayer(self):
        if not Player.CheckLayer('LeftHand'):
            return None, None
        weapon = Player.GetItemOnLayer('LeftHand')
        return self.get_slayer_prop(weapon), weapon

    def find_weapons(self):
        weapons = defaultdict(None)

        for item in search_subcontainers(Player.Backpack):
            slayer = self.get_slayer_prop(item)
            if not slayer:
                continue
            weapons[slayer] = item

        eqslayer, eqw = self.get_equipped_slayer()
        if eqslayer:
            weapons[eqslayer] = eqw
            self.active = sorted(weapons).index(eqslayer) + 1

        return weapons

    def equip_slayer(self, kind):
        while Player.CheckLayer('LeftHand'):
            Player.UnEquipItemByLayer('LeftHand')
            Misc.Pause(625)
        Player.EquipItem(self.slayers[kind])
        Misc.Pause(500)

    def gump(self, progress=False):
        gd = Gumps.CreateGump(True, False, False, False)
        gump_height = 50 + 28 * len(self.slayers)
        Gumps.AddBackground(gd, 0, 0, 160, gump_height, 9270)
        Gumps.AddAlphaRegion(gd, 0, 0, 160, gump_height)
        Gumps.AddLabel(gd, 15, 15, Hue.Cyan, "Slayers available:")

        y_idx = 45
        for btn_id, slayer_type in enumerate(sorted(self.slayers), 1):
            color = (
                Hue.Yellow
                if self.active == btn_id and progress
                else (Hue.Green if self.active == btn_id else Hue.Red)
            )
            Gumps.AddButton(gd, 18, y_idx, 5837, 5838, btn_id, 1, 0)
            Gumps.AddLabel(gd, 48, y_idx, color, slayer_type.capitalize())
            y_idx += 28
            btn_id += 1

        Gumps.SendGump(
            self.gump_id, Player.Serial, 920, 120, gd.gumpDefinition, gd.gumpStrings
        )

    def loop(self):
        while True:
            Misc.Pause(1)
            gd = Gumps.GetGumpData(self.gump_id)
            if gd.buttonid > 0:
                self.active = gd.buttonid
                self.gump(progress=True)
                slayer = sorted(self.slayers)[gd.buttonid - 1]
                self.equip_slayer(slayer)
                self.gump()
                self.slayers = self.find_weapons()


s = Slayer()
s.loop()
