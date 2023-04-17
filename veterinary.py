# the bandage heal agent in razor enhanced fucking sucks.
# this uses the friends agent, with the name "pets".

if Player.GetSkillValue('veterinary') < 100:
    raise Exception('Veterinary skill not found, exiting')

from AutoComplete import *
from lib.util import MobileFilter, Hue

mfilter = MobileFilter(Friend.GetList('pets'), friend=True)


def find_bandage():
    bandages = Items.FindByID(0x0E21, -1, Player.Backpack.Serial, 3)
    if not bandages:
        raise Exception("couldn't find bandages!")
    return bandages


def check_range(pet):
    if not pet:
        raise Exception("invalid pet to check distance")
    return Player.DistanceTo(pet) <= 2


def heal():
    b = find_bandage()
    p = mfilter.get('weakest')

    if p and p.Hits < p.HitsMax * .95 and check_range(p):
        Timer.Create('veterinary', 2200)
        Items.UseItem(b, p)


Timer.Create('veterinary', 1)
Timer.Create('veterinary_err', 1)
while True:
    if Timer.Check('veterinary'):
        Misc.Pause(50)
        continue
    try:
        if not Target.HasTarget() and not Player.Paralized:
            heal()
    except Exception as e:
        if not Timer.Check('veterinary_err'):
            Misc.SendMessage('Error: {}'.format(e), Hue.Red)
            Timer.Create('veterinary_err', 5000)
    finally:
        Misc.Pause(200)
