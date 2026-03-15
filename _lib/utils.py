import random
import subprocess
from typing import TYPE_CHECKING, List, cast

if TYPE_CHECKING:
    import API


NOTORIETY_FRIENDLY = cast(
    List[API.Notoriety], [API.Notoriety.Ally, API.Notoriety.Innocent]
)
NOTORIETY_ENEMY = cast(
    List[API.Notoriety],
    [
        API.Notoriety.Enemy,
        API.Notoriety.Gray,
        API.Notoriety.Murderer,
        API.Notoriety.Criminal,
    ],
)


class ScriptError(Exception):
    def __init__(self, msg: str, hue: int = 32):
        super().__init__(msg)
        self.msg = msg
        self.hue = hue

    def __repr__(self) -> str:
        return f"ScriptError(msg={self.msg!r}, hue={self.hue!r})"


class Hue:
    Black = 1
    Blue = 2122
    Cyan = 90
    Gray = 1000
    Green = 63
    Magenta = 128
    Orange = 2736
    Red = 33
    Yellow = 253
    White = 1150


def p(msg, hue=Hue.White):
    API.SysMsg(str(msg), hue)


def h(msg, serial=API.Player, hue=Hue.White):
    API.HeadMsg(str(msg), serial, hue)


def chebyshev_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    return max(abs(x1 - x2), abs(y1 - y2))


def count_items(graphic: int, container) -> int:
    items = API.FindTypeAll(graphic, container) or []
    return sum(getattr(it, "Amount", 0) or 0 for it in items)


def stop_script(msg: str, hue: int = 32) -> None:
    API.SysMsg(msg, hue)
    API.Stop()


def dismount_if_mounted(delay: float = 0.5) -> None:
    if API.Player and API.Player.Mount:
        API.Dismount()
        API.Pause(delay)


def use_item_on_target(item_serial, target_serial, timeout=2.0, delay=0.5):
    API.UseObject(item_serial)
    if API.WaitForTarget(timeout=timeout):
        API.Target(target_serial)  # type: ignore
        API.Pause(delay)
        return True
    return False


def play_audio(
    path: str = "/usr/share/sounds/ocean/stereo/phone-incoming-call.oga",
):
    subprocess.call(
        [
            "ffplay",
            "-nodisp",
            "-autoexit",
            path,
        ],
    )


def color_paperdoll(hue=0x4000):
    LAYERS = [
        "OneHanded",
        "TwoHanded",
        "Shoes",
        "Pants",
        "Shirt",
        "Helmet",
        "Gloves",
        "Ring",
        "Talisman",
        "Necklace",
        "Hair",
        "Waist",
        "Torso",
        "Bracelet",
        "Face",
        "Beard",
        "Tunic",
        "Earrings",
        "Arms",
        "Cloak",
        "Backpack",
        "Robe",
        "Skirt",
        "Legs",
        "Mount",
    ]
    person = API.FindMobile(API.RequestAnyTarget())  # pyright:ignore
    if not person:
        API.Stop()

    for y in LAYERS:
        item = API.FindLayer(y, person)
        if item:
            item.SetHue(hue)


def wiggle():
    for _ in range(random.randint(8, 16)):
        API.Walk(
            random.choice(
                (
                    "north",
                    "south",
                    "east",
                    "west",
                    "northeast",
                    "northwest",
                    "southeast",
                    "southwest",
                )
            )
        )
        API.Pause(0.1)
