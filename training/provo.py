from typing import List, cast

import API

MaxDistance = 7
ProvokeDelay = 11
Instruments = [0xE9E, 0x2805, 0xE9C, 0xEB3, 0xEB1, 0x0EB2, 0x0E9D]

NOTO = cast(
    List[API.Notoriety],
    [API.Notoriety.Gray, API.Notoriety.Criminal, API.Notoriety.Enemy],
)


def FindInstrument():
    for item in Instruments:
        instrument = API.FindType(item, API.Backpack)
        if instrument:
            return instrument
    return None


while True:
    instrument = FindInstrument()
    if not instrument:
        API.SysMsg("No instrument found in backpack.", 32)
        break

    target1 = API.NearestMobile(NOTO, MaxDistance)
    if not target1:
        API.SysMsg("No valid targets found.", 32)
        break

    API.HeadMsg("Target 1", target1)
    API.IgnoreObject(target1)

    target2 = API.NearestMobile(NOTO, MaxDistance)
    if not target2:
        API.SysMsg("No valid targets found.", 32)
        break

    API.IgnoreObject(target2)
    API.HeadMsg("Target 2", target2)

    API.UseSkill("Provocation")
    API.WaitForTarget()

    if API.InJournal("What instrument"):
        API.Target(instrument)  # pyright: ignore
        API.WaitForTarget()

    API.Target(target1)  # pyright: ignore
    API.WaitForTarget()
    API.Target(target2)  # pyright: ignore
    API.Pause(ProvokeDelay)
    API.ClearIgnoreList()
    API.ClearJournal()
