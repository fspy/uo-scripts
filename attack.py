# create a friends list called 'pets' and add your pets there.
# `use_honor` will try to use honor before sending pet
# `dismount` assumes your pet is your mount, so it dismounts
use_honor = True
dismount = True

from AutoComplete import *

mobile_filter = Mobiles.Filter()
mobile_filter.Friend = True
mobile_filter.Serials = Friend.GetList('pets')


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

    if dismount:
        if Player.Mount:
            Mobiles.UseMobile(Player.Serial)
            while Player.Mount:
                Misc.Pause(200)

    pet = Mobiles.Select(Mobiles.ApplyFilter(mobile_filter), 'nearest')
    if not pet:
        Player.HeadMessage(33, 'Unable to find a pet!')
        return

    while Misc.WaitForContext(pet, 2000, False):
        Misc.ContextReply(pet, 1)
        _execute(target)
        return


pet_attack(use_honor, dismount)
