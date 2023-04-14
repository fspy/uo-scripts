# the bandage heal agent in razor enhanced fucking sucks.
# this uses the friends agent, with the name "pets".

from AutoComplete import *


def find_bandage():
    bandages = Items.FindByID(0x0E21, -1, Player.Backpack.Serial, 3)
    if not bandages:
        raise Exception("couldn't find bandages!")
    return bandages


def find_most_damaged_pet():
    mfilter = Mobiles.Filter()
    mfilter.Friend = True
    mfilter.Serials = Friend.GetList('pets')

    found_pets = Mobiles.ApplyFilter(mfilter)
    if not found_pets:
        raise Exception("couldn't find any pets!")
    return Mobiles.Select(found_pets, 'Weakest')


def check_range(pet):
    if not pet:
        raise Exception("invalid pet to check distance")
    return Player.DistanceTo(pet) <= 2


def heal():
    b = find_bandage()
    p = find_most_damaged_pet()

    if p.Hits < p.HitsMax * .95 and check_range(p):
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
            #Misc.SendMessage('Error: {}'.format(e), 33)
            Timer.Create('veterinary_err', 5000)
    finally:
        Misc.Pause(200)
