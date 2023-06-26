from AutoComplete import *

from lib.util import MobileFilter

f = MobileFilter(max_range=2, notorieties=[1, 2])

Journal.Clear('owner has been asked to sanctify')
while True:
    mob = f.get('Weakest')
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
