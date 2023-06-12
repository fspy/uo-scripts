from AutoComplete import *
from System import Byte
from System.Collections.Generic import List

f = Mobiles.Filter()
f.RangeMax = 2
f.Notorieties = List[Byte](bytes([1, 2]))

Journal.Clear('owner has been asked to sanctify')
while True:
    mob = Mobiles.Select(Mobiles.ApplyFilter(f), 'Weakest')
    if not mob:
        Misc.Pause(1000)
        continue
    if Items.UseItemByID(0x0E21, -1):
        Target.WaitForTarget(3000)
        Target.TargetExecute(mob.Serial)
        Misc.Pause(3000)
        if Journal.Search('owner has been asked to sanctify'):
            Journal.Clear('owner has been asked to sanctify')
            Misc.Pause(60000)
    else:
        Misc.SendMessage('Out of bandages!')
