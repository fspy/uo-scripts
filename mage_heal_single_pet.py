pet_id = Target.PromptTarget('PET')
pet = Mobiles.FindBySerial(pet_id)
lag = 200

# cast helper
def cast(spell, target, wait=3000):
    Spells.Cast(spell)
    Target.WaitForTarget(wait, True)
    Target.TargetExecute(target)
    Misc.Pause(lag)

while not pet.IsGhost:
    if pet.Poisoned:
        cast('Arch Cure', pet)
        continue
    if pet.Hits < pet.HitsMax * .9:
        cast('Greater Heal', pet)
        continue