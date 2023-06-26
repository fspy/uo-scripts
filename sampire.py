from AutoComplete import *
from System import Byte
from System.Collections.Generic import List


def mobs_list(range=6):
    fil = Mobiles.Filter()
    fil.Enabled = True
    fil.RangeMax = range
    fil.Notorieties = List[Byte](bytes([3, 4, 5, 6]))
    fil.IsGhost = False
    fil.Friend = False
    mobs = Mobiles.ApplyFilter(fil)

    return sorted(mobs, key=Player.DistanceTo)


use_eoo = False
use_df = False
use_cw = False
use_ls = False
use_ca = True
use_honor = False

default_pause = 200


Journal.FilterText('Setting ability')
Journal.FilterText('You cannot perform this special')
Journal.FilterText('You are already casting a spell')
Journal.FilterText('You have not yet recovered from')


def fighting(focus, aoe=True):

    Player.Attack(focus)

    if use_eoo and 'Enemy Of One' not in Player.Buffs and Player.Mana >= 12:
        Spells.CastChivalry('Enemy Of One')
        while Player.Paralized:
            Misc.Pause(default_pause)

    if use_df and 'Divine Fury' not in Player.Buffs and Player.Mana >= 8:
        Spells.CastChivalry('Divine Fury')
        while Player.Paralized:
            Misc.Pause(default_pause)

    if use_cw and 'Consecrate Weapon' not in Player.Buffs and Player.Mana >= 6:
        Spells.CastChivalry('Consecrate Weapon')
        while Player.Paralized:
            Misc.Pause(default_pause)

    if use_ca and 'Counter Attack' not in Player.Buffs and 'Evasion' not in Player.Buffs:
        Spells.CastBushido('Counter Attack')
        while Player.Paralized:
            Misc.Pause(default_pause)

    if aoe:
        if not Player.HasSpecial and Player.Mana > 18:
            Player.WeaponSecondarySA()
    else:
        if use_ls:
            if not Player.SpellIsEnabled('Lightning Strike') and Player.Mana >= 6:
                Spells.CastBushido('Lightning Strike')
        else:
            if not Player.HasSpecial and Player.Mana >= 25:
                Player.WeaponPrimarySA()


while not Player.IsGhost and Player.Visible:
    victims = mobs_list()
    if not victims:
        Misc.Pause(default_pause)
        continue

    if use_honor == 1:
        Journal.Clear('Honorable')
        Player.InvokeVirtue("Honor")
        Target.WaitForTarget(1000)
        Target.TargetExecute(victims[0])
        Journal.WaitJournal('Honorable', 1000)

    while Mobiles.FindBySerial(victims[0].Serial) and Player.DistanceTo(victims[0]) < 2:
        fighting(victims[0], len(mobs_list(1)) > 1)
        Misc.Pause(default_pause)
