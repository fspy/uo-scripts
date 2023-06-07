from System.Collections.Generic import List
from System import Byte


def mobs_list (range):
    fil = Mobiles.Filter()
    fil.Enabled = True
    fil.RangeMax = range
    fil.Notorieties = List[Byte](bytes([3,4,5,6]))
    fil.IsGhost = False
    fil.Friend = False
    mobs = Mobiles.ApplyFilter(fil)
    return mobs

use_eoo = 0
use_df = 0
use_cw = 1
ls_or_ability = 2 # ls == 1
use_honor = 1

        
def fighting(enemy): 
    Player.Attack(nearest)  
    if 'Enemy Of One' not in Player.Buffs and use_eoo == 1 and Player.Mana >= 12:
        Spells.CastChivalry('Enemy Of One')
        Misc.Pause(50)
    elif 'Divine Fury' not in Player.Buffs and use_df == 1 and Player.Mana >= 8:
        Spells.CastChivalry('Divine Fury')
        Misc.Pause(50)
    elif 'Consecrate Weapon' not in Player.Buffs and use_cw == 1 and Player.Mana >= 6:
        Spells.CastChivalry('Consecrate Weapon')
        Misc.Pause(50)
    else:
        if nearby_enemies_len == 1:
            if ls_or_ability == 1:
                if not Player.SpellIsEnabled('Lightning Strike') and Player.Mana >= 6:
                    Spells.CastBushido('Lightning Strike')
            elif ls_or_ability == 2:
                if not Player.HasSpecial and Player.Mana >= 25:
                    Player.WeaponPrimarySA()
            Misc.Pause(50)
        elif nearby_enemies_len >= 2:
            if not Player.HasSpecial and Player.Mana > 16:
                Player.WeaponSecondarySA()


while not Player.IsGhost and Player.Visible:
    victims = mobs_list(6)
    if len(victims) > 0:
        nearest = Mobiles.Select(victims, 'Nearest')
        if use_honor == 1:
            Journal.Clear()
            Player.InvokeVirtue("Honor")
            Target.WaitForTarget(1000)
            Target.TargetExecute(nearest)
            Journal.WaitJournal('Honorable',1000)
        
        while Mobiles.FindBySerial(nearest.Serial) and Player.DistanceTo(nearest) <= 6:
            nearby_enemies_len = len(mobs_list(1))
            fighting(nearest)
            Misc.Pause(50)
    else:
        Misc.Pause(50)