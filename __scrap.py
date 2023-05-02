import sys

from AutoComplete import *

from lib.caster_training import *


def useskill(skillname='Tracking', pause=10500):
    while Player.GetSkillValue(skillname) < Player.GetSkillCap(skillname):
        print(skillname)
        Player.UseSkill(skillname)
        if skillname == 'Tracking':
            Gumps.WaitForGump(2976808305, 3000)
            Gumps.SendAction(2976808305, 1)
            Gumps.WaitForGump(2976808305, 3000)
            Gumps.CloseGump(2976808305)
        Misc.Pause(pause)


def vendor_price(price):
    while not Journal.Search('in a price and description for'):
        Misc.Pause(50)
        continue
    Misc.ResponsePrompt('\n{}\n'.format(price))
    Misc.SendMessage('priced!', 52)
    Journal.Clear('in a price and description for')
    Misc.Pause(200)


# MageryTrainer(safe_spell=Spell('Greater Heal', 12, Player.Serial)).run()

useskill('Hiding')