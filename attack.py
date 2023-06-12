# create a friends list called 'pets' and add your pets there.
# `use_honor` will try to use honor before sending pet
# `dismount` assumes your pet is your mount, so it dismounts
from AutoComplete import *

from lib.util import Hue, MobileFilter

use_honor = True
dismount = True


mf = MobileFilter(serials=Friend.GetList('pets'), friend=True)


def pet_attack(honor=True, dismount=True):

    def _execute(target):
        Target.WaitForTarget(2000, True)
        Target.TargetExecute(target)
        Misc.Pause(200)

    target = Target.GetTargetFromList('enemy')
    if not target:
        Player.HeadMessage(90, 'No enemies around!')
        return

    Mobiles.Message(target, 1100, "- TARGET -")

    if honor:
        Player.InvokeVirtue('Honor')
        _execute(target)

    if dismount and Player.Mount:
        Mobiles.UseMobile(Player.Serial)
        while Player.Mount:
            Misc.Pause(50)

    pet = mf.get('Nearest')
    if not pet:
        Player.HeadMessage(Hue.Red, 'Unable to find a pet!')
        return

    Misc.UseContextMenu(pet.Serial, "Command: Kill", 1000)
    _execute(target)
    return


pet_attack(use_honor, dismount)
