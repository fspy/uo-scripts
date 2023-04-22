from AutoComplete import *


def useskill(skillname='Tracking'):
    while Player.GetSkillValue(skillname) < Player.GetSkillCap(skillname):
        Player.UseSkill(skillname)
        Gumps.WaitForGump(2976808305, 3000)
        Gumps.SendAction(2976808305, 1)
        Misc.Pause(10000)


def vendor_price(price):
    while not Journal.Search('in a price and description for'):
        Misc.Pause(50)
        continue
    Misc.ResponsePrompt('\n{}\n'.format(price))
    Misc.SendMessage('priced!', 52)
    Journal.Clear('in a price and description for')
    Misc.Pause(200)


from lib.caster_training import MageryTrainer, MysticismTrainer, SpellweavingTrainer


MageryTrainer().run()
MysticismTrainer().run()
SpellweavingTrainer().run()


while True:
    #Spells.CastMastery('Shadow')
    Player.UseSkill('hiding')
    Misc.Pause(10500)
    
    
    
    
    
    
    
    
    
    