from AutoComplete import *
import re
from System.Collections.Generic import List

# find pet -> range warning
# find bandage -> setting?
# gift of life
# gift of renewal
# remove poison
# greater heal
# thresholds


class PetHealing:
    def __init__(self, friend_list):

        mf = Mobiles.Filter()
        mf.Serials = Friend.GetList(friend_list)

        self.filter = mf
        self.pet = self.get_pet()

        self.detect_features()

    def get_pet(self):
        pets = Mobiles.ApplyFilter(self.filter)
        pet = Mobiles.Select(pets, 'nearest')
        if not pet:
            Misc.SendMessage(
                'unable to find a pet, try dismounting or the stables!')
        return pet

    def detect_features(self):
        if Player.GetSkillValue('Veterinary') > 80:
            self.veterinary = True

        if Player.GetSkillValue('Spellweaving') > 75.5:
            # 75.5 => 100% gift of life
            self.spellweaving = True

            crystal: Item = Items.FindByID(
                0x3155, 0, Player.Backpack.Serial, True)

            if not crystal:
                Misc.SendMessage(
                    'you have spellweaving but no crystal! go get one!')
                return

            crystal_strength = crystal.Properties.Find(
                lambda x: x.Number == 1060485)

            match = re.search('(\d+)$', crystal_strength.ToString())
            if match:
                self.spellweaving_level = int(match.group())


ph = PetHealing('pets')

print(ph.pet.Name, ph.spellweaving, ph.spellweaving_level, ph.veterinary)

# while True:
#     if Player.IsGhost:
#         Misc.Pause(100)
#         continue
