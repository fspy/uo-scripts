from typing import List, cast

import API

MaxDistance = 12
ProvokeDelay = 11
DiscordDelay = 7
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

    targets = API.GetAllMobiles(notoriety=NOTO, distance=10)
    if len(targets) < 1:
        API.Pause(1)
        continue

    for t in targets:
        while True:
            API.ClearJournal()
            API.HeadMsg("Disco!", t)
            API.UseSkill("Discordance")
            API.WaitForTarget()
            API.Target(t)  # pyright:ignore
            API.Pause(0.5)

            if API.InJournalAny(["already in discord", "too far away"]):
                API.Pause(1)
                break

            if API.InJournal("You attempt to disrupt"):
                API.Pause(5)
                continue

            if API.InJournal("You play jarring music"):
                API.Pause(7)
                break

    API.CastSpell("Invisibility")
    API.WaitForTarget()
    API.TargetSelf()
    API.Pause(30)

    if API.InJournal("What instrument"):
        API.Target(instrument)  # pyright: ignore
        API.WaitForTarget()
