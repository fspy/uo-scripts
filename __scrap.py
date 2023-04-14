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


def train_weaving():
    from lib.caster_training import CasterTraining, SpellSafe, Spell

    heal = Spell('Greater Heal', 20, Player.Serial)
    ct = CasterTraining(
        'Spellweaving', {
            120:
            SpellSafe('Word of Death', 50, Player.Serial, heal)
        })
    ct.run()

    
def train_magery():
    from lib.caster_training import CasterTraining, SpellSafe, Spell
    
    heal = Spell('Heal', 4, Player.Serial)
    ct = CasterTraining(
        'Magery', {
            45: SpellSafe('Fireball', 9, Player.Serial, heal),
            55: SpellSafe('Lightning', 11, Player.Serial, heal),
            65: Spell('Magic Reflection', 14, Player.Serial),
            75: Spell('Reveal', 20, Player.Serial),
            90: SpellSafe('Flamestrike', 40, Player.Serial, heal),
            120: Spell('Earthquake', 50)
        })
    ct.run()

    
def train_necro():
    from lib.caster_training import CasterTraining, SpellSafe, Spell

    ct = CasterTraining(
        'Necromancy', {
            50: Spell('Pain Spike', 5, Player.Serial),
            70: Spell('Horrific Beast', 11),
            90: Spell('Wither', 23),
            100: Spell('Lich Form', 25),
            120: Spell('Vampiric Embrace', 25),
        })
    ct.run()
    

train_magery()
train_necro()
while True:
    #Spells.CastMastery('Shadow')
    Player.UseSkill('hiding')
    Misc.Pause(10500)
    
    
    
    
    
    
    
    
    
    