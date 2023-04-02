use_honor = True
dismount = True
debug = False

mobile_filter = Mobiles.Filter()
mobile_filter.Friend = True
mobile_filter.Serials = Friend.GetList('pets')


def pet_attack(honor=True, dismount=True):

    def _execute(target):
        Target.WaitForTarget(2000, True)
        Target.TargetExecute(target)
        Misc.Pause(200)

    # acquire target
    target = Target.GetTargetFromList('enemy')
    if not target:
        Player.HeadMessage(90, 'No enemies around!')
        return

    if debug:
        print('1 got target')
    Mobiles.Message(target, 1100, "- TARGET -")

    if honor:
        Player.InvokeVirtue('Honor')
        _execute(target)

    if debug:
        print('2 honored')
    if dismount:
        if Player.Mount:
            Mobiles.UseMobile(Player.Serial)
            while Player.Mount:
                Misc.Pause(200)
        if debug:
            print('3 dismounted')

    pet = Mobiles.Select(Mobiles.ApplyFilter(mobile_filter), 'nearest')
    if not pet:
        Player.HeadMessage(33, 'Unable to find a pet!')
        return

    if debug:
        print('4 got pet')
    while Misc.WaitForContext(pet, 2000, False):
        Misc.ContextReply(pet, 1)
        _execute(target)
        if debug:
            print('5 attacked')
        return


pet_attack(use_honor, dismount)
