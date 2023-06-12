import re
from collections import defaultdict, namedtuple

from AutoComplete import *

from lib.util import Hue, search_subcontainers, show_props

SkillValue = namedtuple("Skill", ["Name", "Value"])


class Slayer:
    gump_id = 835374663

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
        # self.skill = self.detect_skill()
        self.slayers = self.find_weapons()

    # def detect_skill(self):
    #     skills = ["Magery", "Necromancy", "Swords"]
    #     result = SkillValue(None, 0)
    #     for s in skills:
    #         val = Player.GetSkillValue(s)
    #         if val > result.Value:
    #             result = SkillValue(s, val)
    #     return result.Name

    def _get_slayer(self, item):
        if any(prop.Number == 0x103134 for prop in item.Properties):
            # 0x103134 swordsmanship
            for prop in item.Properties:
                if prop.Number in self.ids:
                    return prop.ToString()
        return None

    def _unequip(self, layer="LeftHand"):
        while Player.CheckLayer(layer):
            Player.UnEquipItemByLayer(layer)
            Misc.Pause(625)

    def find_weapons(self):
        self._unequip()
        weapons = defaultdict(None)
        for item in search_subcontainers(Player.Backpack):
            slayer = self._get_slayer(item)
            if not slayer:
                continue
            key = re.sub(r"(.+?)( slayer)?$", r"\1", slayer).lower()
            weapons[key] = item
        return weapons

    def equip_slayer(self, kind):
        self._unequip()
        Player.EquipItem(self.slayers[kind])
        Misc.Pause(200)

    def gump(self, active=0, progress=False):
        gd = Gumps.CreateGump(True, False, True, False)
        gump_height = 50 + 28 * len(self.slayers)
        Gumps.AddBackground(gd, 0, 0, 160, gump_height, 9270)
        Gumps.AddAlphaRegion(gd, 0, 0, 160, gump_height)
        Gumps.AddLabel(gd, 15, 15, Hue.Cyan, "Slayers available:")

        y_idx = 45
        for btn_id, slayer_type in enumerate(sorted(self.slayers), 1):
            color = (
                Hue.Yellow
                if active == btn_id and progress
                else (Hue.Green if active == btn_id else Hue.Red)
            )
            Gumps.AddButton(gd, 18, y_idx, 5837, 5838, btn_id, 1, 0)
            Gumps.AddLabel(gd, 48, y_idx, color, slayer_type.capitalize())
            y_idx += 28
            btn_id += 1

        Gumps.SendGump(
            self.gump_id, Player.Serial, 920, 120, gd.gumpDefinition, gd.gumpStrings
        )

    def loop(self):
        active = 0
        while True:
            self.gump(active)
            Misc.Pause(500)
            gd = Gumps.GetGumpData(self.gump_id)
            if gd.buttonid > 0:
                active = gd.buttonid
                self.gump(active, True)
                slayer = sorted(self.slayers)[gd.buttonid - 1]
                self.equip_slayer(slayer)
                self.gump(active)
            else:
                Gumps.SendAction(self.gump_id, 0)


# show_props()
s = Slayer()
s.loop()
