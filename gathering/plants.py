import re
from time import time

import API

PLANT_MAIN_GUMP = 0xA9B90129
PLANT_RESOURCE_GUMP = 0x66E3F765
PLANT_CONFIRM_GUMP = 0xDD77BD84


def wait_gump_timeout(gump, timeout=3):
    start = time()
    while not API.HasGump(gump):
        if time() - start > timeout:
            return
        API.Pause(0.1)


def wait_and_reply(gump, button, timeout=3):
    wait_gump_timeout(gump, timeout)
    API.ReplyGump(button, gump)


def process_plants(destroy=False):
    plant_regex = re.compile(r"^a vibrant .+ (?:plant|tree|bush)", re.I)
    plants = [x for x in safe_get_items(3) if plant_regex.match(x.Name)]
    for plant in plants:
        API.UseObject(plant)

        wait_gump_timeout(PLANT_MAIN_GUMP)
        wait_and_reply(PLANT_MAIN_GUMP, 1)

        resources, seeds = parse_resources()

        if resources[0] > 0:
            wait_and_reply(PLANT_RESOURCE_GUMP, 7)
            resources, _ = parse_resources()

        if seeds[0] > 0:
            wait_and_reply(PLANT_RESOURCE_GUMP, 8)
            _, seeds = parse_resources()

        if destroy:
            wait_and_reply(PLANT_RESOURCE_GUMP, 2)
            wait_and_reply(PLANT_CONFIRM_GUMP, 3)
            API.IgnoreObject(plant.Serial)
            continue

        if resources[1] == 0 and seeds[1] == 0:
            wait_and_reply(PLANT_RESOURCE_GUMP, 2)
            wait_and_reply(PLANT_CONFIRM_GUMP, 3)
        else:
            wait_and_reply(PLANT_RESOURCE_GUMP, 0)

        plant.SetHue(0x4000)
        API.IgnoreObject(plant.Serial)
        API.Pause(0.1)


def parse_resources():
    wait_gump_timeout(PLANT_RESOURCE_GUMP)

    raw = API.GetGump(PLANT_RESOURCE_GUMP).PacketGumpText
    match = re.search(r"(?<resources>\d/\d|X)\n(?<seeds>\d/\d|X)", raw)
    if not match:
        return (0, 0), (0, 0)

    def parse_value(val):
        if val == "X":
            return (0, 0)
        parts = val.split("/")
        return (int(parts[0]), int(parts[1]))

    return parse_value(match.group("resources")), parse_value(match.group("seeds"))


def safe_get_items(*args):
    try:
        result = API.GetItemsOnGround(*args)
        return result if result is not None else []
    except Exception:
        return []


def free_garden_beds():
    try:
        garden_beds = {b for b in safe_get_items(3) if 0x4B22 <= b.Graphic <= 0x4B2A}
        plant_positions = {(p.X, p.Y) for p in safe_get_items(3, 0x0913)}
        API.HeadMsg(
            "beds: {}, plants: {}".format(len(garden_beds), len(plant_positions)),
            0,
            1337,
        )
    except Exception as e:
        API.HeadMsg("free_garden_beds failed: {}".format(e), 0, 1337)
        return

    for b in garden_beds:
        if (b.X, b.Y) not in plant_positions:
            yield b


def plant_seeds():
    for bed in free_garden_beds():
        seeds = API.FindTypeAll(0x0DCF, API.Backpack)
        if not seeds:
            API.HeadMsg("out of seeds", 0, 1337)
            return
        try:
            API.UseType(0x0DCF, container=API.Backpack)
            API.WaitForTarget(timeout=0.5)
            API.Target(bed.Serial)  # pyright:ignore
            API.Pause(0.1)
        except Exception as e:
            API.HeadMsg("plant failed: {}".format(e), 0, 1337)
            continue


try:
    API.ClearIgnoreList()
    while not API.StopRequested:
        plant_seeds()
        process_plants()
        API.Pause(0.1)

except Exception as e:
    API.SysMsg(f"Error? {e}", 36)
finally:
    API.SysMsg("plants: stopped")
