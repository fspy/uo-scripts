# will make your game freeze from healing your pet non-stop with magery

from AutoComplete import *
from lib.util import MobileFilter, safe_cast, Hue

lag = 150
mf = MobileFilter(Friend.GetList('pets'), friend=True)


def heal(pet, threshold=0.5):
    if pet.Poisoned:
        safe_cast('Arch Cure', pet)
        Misc.Pause(lag)  # cure animation
        return
    if pet.Hits < pet.HitsMax * threshold:
        while pet.Hits < pet.HitsMax and not pet.Poisoned and not pet.YellowHits:
            safe_cast('Greater Heal', pet)
    Misc.Pause(lag)


Misc.SendMessage('Auto Pet Healing Enabled!', Hue.Green)
while True:
    pet = mf.get('Weakest')
    if not pet:
        Player.HeadMessage(33, 'Pet not found!')
        Misc.Pause(lag)
    if not pet.IsGhost and Player.DistanceTo(pet) < 10:
        heal(pet, 0.5)
