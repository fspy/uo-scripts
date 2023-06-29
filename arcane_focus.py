DELAY_IN_SECONDS = 60

from AutoComplete import *

Timer.Create("arcane_focus", 1)
skill = Player.GetSkillValue("spell weaving")

while skill > 0:
    if not Timer.Check("arcane_focus"):  # timer has expired
        if not next(
            (i for i in Player.Backpack.Contains if i.Name == "Arcane Focus"), None
        ):
            for i in range(3):
                Misc.Beep()
                Misc.SendMessage("No Arcane Focus!!", 33)
                Player.HeadMessage(33, "No Arcane Focus!!")
                Misc.Pause(250 * (i + 1))

        Timer.Create("arcane_focus", DELAY_IN_SECONDS * 1000)
    Misc.Pause(1000)
