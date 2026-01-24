# pyright: reportCallIssue=false
import time

import API
from _lib.utils import p


def spell_toggle(spell):
    while not API.StopRequested:
        API.CastSpell(spell)
        API.WaitForTarget(timeout=2)
        API.Target(API.LastTargetSerial)
        API.Pause(1)
        API.CastSpell(spell)


def hiding():
    while API.GetSkill("Hiding").Base < API.GetSkill("Hiding").Cap:
        API.UseSkill("Hiding")
        API.Pause(1)


def chest_check():
    chest_graphics = {0x0E40, 0x0E41}
    chest_hues = {0, 1109}  # , 1150, 2219, 2207}
    container = API.RequestTarget(10)

    for cg in chest_graphics:
        chests = API.FindTypeAll(cg, container)
        chests = filter(lambda c: c.Hue in chest_hues, chests)
        for chest in chests:
            API.MoveItem(chest, API.Backpack, 1)
            # API.HeadMsg(f"{chest.Hue}", chest.Serial, chest.Hue)
            # API.HeadMsg(f"{hex(chest.Graphic)}", chest.Serial)
            API.Pause(0.65)

        API.Pause(0.65)


def auto_coown():
    while not API.StopRequested:
        if API.HasGump(0x29B6C49):
            p("set permission to co-owner!")
            API.ReplyGump(2)
        API.Pause(0.1)


def grab_horned_kit():
    API.ContextMenu(0xC1269, 3)
    API.WaitForGump(0x69DA8520)
    API.ReplyGump(222, 0x69DA8520)


def grab_copper_hammer():
    API.ContextMenu(0xC1068, 3)
    API.WaitForGump(0x69DA8520)
    API.ReplyGump(223, 0x69DA8520)


def grab_bronze_hammer():
    API.ContextMenu(0xC1068, 3)
    API.WaitForGump(0x69DA8520)
    API.ReplyGump(225, 0x69DA8520)
