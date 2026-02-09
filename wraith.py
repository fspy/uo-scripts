import API
from _lib.utils import Hue, p

default_necro = "Main", "Necro"

WRAITH_SCROLL = 0x226F
WRAITH_FORMS = [0x02EB]


def main():
    if API.FindType(WRAITH_SCROLL, API.Backpack):
        API.UseObject(API.Found)
        return

    if default_necro[1] not in API.GetAvailableDressOutfits():
        p("[wraith]: outfit not found", Hue.Magenta)
        return

    is_wraith = API.Player.Graphic in WRAITH_FORMS

    API.Dress(default_necro[1])
    while API.IsProcessingMoveQueue():
        API.Pause(0.1)

    API.CastSpell("Wraith Form")
    while API.BuffExists("Wraith Form") == is_wraith:
        API.Pause(0.1)

    API.Dress(default_necro[0])


main()
