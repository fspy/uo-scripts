# will make your game freeze from healing your pet non-stop with magery

from AutoComplete import *
from lib.util import safe_cast

pet_id = Target.PromptTarget('PET')
pet = Mobiles.FindBySerial(pet_id)

while not pet.IsGhost:
    if pet.Poisoned:
        safe_cast('Arch Cure', pet)
        continue
    if pet.Hits < pet.HitsMax * .9:
        safe_cast('Greater Heal', pet)