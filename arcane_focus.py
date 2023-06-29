DELAY_IN_SECONDS = 60

Timer.Create('arcane_focus', 1)
while Player.GetSkillValue('spell weaving') > 0:
    if Timer.Check('arcane_focus'): # timer hasn't run out, don't do anything
        Misc.NoOperation()
        continue
    if not Items.FindByName('Arcane Focus', 0, Player.Backpack.Serial, True):
        for i in range(3): 
            Misc.Beep()
            Misc.SendMessage('No Arcane Focus!!', 33)
            Player.HeadMessage(33, 'No Arcane Focus!!')
            Misc.Pause(250 * (i + 1))
    Timer.Create('arcane_focus', DELAY_IN_SECONDS * 1000)