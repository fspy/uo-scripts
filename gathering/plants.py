from time import time

import API
from _lib.utils import ScriptError, p

PLANT_TYPES = (
    0x0C83,
    0x0C9F,
    0x0CA5,
    0x0CFB,
    0x0D27,
    0x246C,
    0x28E1,
)

PLANT_MAIN_GUMP = 0xA9B90129
PLANT_RESOURCE_GUMP = 0x66E3F765
PLANT_CONFIRM_GUMP = 0xDD77BD84


def wait_gump_timeout(gump, timeout=3):
    start = time()
    while not API.HasGump(gump):
        if time() - start > timeout:
            return  # raise ScriptError("gump timeout")
        API.Pause(0.1)


def wait_and_reply(gump, button, timeout=3):
    wait_gump_timeout(gump, timeout)
    API.ReplyGump(button, gump)


def process_plants():
    plants = (x for x in API.GetItemsOnGround(3) if x.Graphic in PLANT_TYPES)
    for plant in plants:
        API.UseObject(plant)
        wait_gump_timeout(PLANT_MAIN_GUMP)

        # check if done
        # might be wrong (need to check for X in resources & seeds)
        gump_contents = API.GetGumpContents(PLANT_MAIN_GUMP)
        plant_status = int(gump_contents.split()[-3])
        if plant_status > 8:
            wait_and_reply(PLANT_MAIN_GUMP, 1)
            wait_and_reply(PLANT_RESOURCE_GUMP, 2)
            wait_and_reply(PLANT_CONFIRM_GUMP, 3)
            continue

        # grab resources
        wait_and_reply(PLANT_MAIN_GUMP, 1)
        wait_and_reply(PLANT_RESOURCE_GUMP, 7)
        wait_and_reply(PLANT_RESOURCE_GUMP, 8)
        wait_and_reply(PLANT_RESOURCE_GUMP, 0)

        plant.SetHue(0x4000)
        API.IgnoreObject(plant.Serial)
        API.Pause(0.1)


try:
    API.ClearIgnoreList()
    while not API.StopRequested:
        process_plants()
        API.Pause(0.1)
except ScriptError as e:
    p(e.msg, e.hue)
except SystemError:
    p("stopped")
