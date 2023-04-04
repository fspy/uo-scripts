# this sucks, don't use it

import threading
from AutoComplete import *
import re, time
from lib.colors import colors
from lib.util import safe_cast

settings = {
    'veterinary': True,
    'magery': True,
    'gift_of_renewal': True,
    'gift_of_life': 'pet',
    'health_trigger': 95,
}


class PetHealing:

    RENEWAL_BASE_DURATION = 30 * 1000  # (30s in milliseconds)
    RENEWAL_COOLDOWN = 30 * 1000  # (30s in milliseconds)
    VETERINARY_DELAY = 3000
    DELAY = 200

    def __init__(self,
                 friend_list,
                 health_trigger=95,
                 veterinary=True,
                 magery=True,
                 gift_of_renewal=True,
                 gift_of_life='self'):
        mf = Mobiles.Filter()
        mf.Serials = Friend.GetList(friend_list)

        self.filter = mf
        self.pet = self.get_pet()
        self.health_trigger = float(health_trigger)

        self.player_veterinary = Player.GetSkillValue('Veterinary')
        self.player_spellweaving = Player.GetSkillValue('Spellweaving')
        self.player_magery = Player.GetSkillValue('Magery')

        self.features(veterinary, magery, gift_of_renewal, gift_of_life)

    def get_pet(self):
        pets = Mobiles.ApplyFilter(self.filter)
        pet = Mobiles.Select(pets, 'nearest')
        if not pet:
            Misc.SendMessage(
                'unable to find a pet, try dismounting or the stables!')
        return pet

    def features(self, vet, magery, renewal, life):
        if self.player_veterinary > 80 and vet:
            self.veterinary = True
            Timer.Create('ph_vet', 1)

        if self.player_spellweaving > 75.5 and (renewal or life):
            if renewal:
                self.gift_of_renewal = True
                Timer.Create('ph_renewal', 1)
            if life:
                self.gift_of_life = self.pet.Serial if life == 'pet' else Player.Serial
                self._last_life = 0

            focus = Items.FindByID(0x3155, 0, Player.Backpack.Serial, True)
            if not focus:
                Misc.SendMessage(
                    'you have spellweaving but no focus! go get one!')
                return

            focus_strength = focus.Properties.Find(
                lambda x: x.Number == 1060485)

            match = re.search('(\d+)$', focus_strength.ToString())
            if not match:
                Misc.SendMessage("couldn't identify focus strength...?")
                return

            self.focus_strength = int(match.group())

            # 30s base duration + 10s per focus level + 30s cooldown
            self.renewal_duration = 30 + (self.focus_strength * 10) + 30

            # sw * 10 / 120 + focus (in minutes)
            duration_m = (float(self.player_spellweaving) * 10 /
                          120) + self.focus_strength

            # in seconds
            self.life_duration = int(duration_m * 60)

        if self.player_magery > 64 and magery:
            self.magery = True

    def use_bandages(self):
        if Timer.Check('ph_vet'):
            return

        bandage = Items.FindByID(0x0E21, -1, Player.Backpack.Serial)
        if not bandage:
            Misc.SendMessage('no bandages!')
            return

        if self.pet.DistanceTo(Mobiles.FindBySerial(Player.Serial)) <= 2:
            Items.UseItem(bandage.Serial, self.pet.Serial, 3000)
            Misc.Pause(self.DELAY)
            if Journal.Search('begin applying the bandages'):
                Timer.Create('ph_vet', self.VETERINARY_DELAY)

    def _gol_thread(self):
        if not safe_cast('Gift of Life', self.gift_of_life):
            return

        Misc.Pause(self.DELAY)
        if Journal.Search('weave powerful magic, protecting'):
            Player.HeadMessage(
                colors['green'], 'Gift of Life active for {} minutes!'.format(
                    round(self.life_duration / 60)))
            self._last_life = time.time()
            return
        elif Journal.Search('is already in effect'):
            if time.time() - self._last_life >= self.life_duration:
                # try again in 30s
                Player.HeadMessage(colors['red'],
                                   'Gift of Life is already active!')
                self._last_life = time.time() + 30
                threading.Timer(30, self._gol_thread).start()

    def use_gift_of_life(self):
        if time.time() - self._last_life < self.life_duration:
            return

        threading.Thread(target=self._gol_thread).start()

    def use_gift_of_renewal(self):
        if Timer.Check('ph_renewal'):
            return

        if not safe_cast('Gift of Renewal', self.pet.Serial):
            Misc.SendMessage('unable to cast gift of renewal')
            return

        Misc.Pause(self.DELAY)
        if Journal.Search('is already in effect') or Journal.Search(
                'must wait before trying'):
            # retry in 10s
            Timer.Create('ph_renewal', 10000)
            self._last_life = time.time()
            Player.HeadMessage(
                colors['red'],
                'Gift of Renewal is already active / on cooldown!')
            return

        Timer.Create('ph_renewal', self.renewal_duration * 1000)
        Player.HeadMessage(
            colors['green'], 'Gift of Renewal ative for {} seconds!'.format(
                self.renewal_duration - 30))

    def use_magery(self, cure_only=False):
        if self.pet.Poisoned:
            safe_cast('Arch Cure', self.pet)
        if not cure_only:
            safe_cast('Greater Heal', self.pet)

    def check_health(self):
        health = self.pet.Hits / self.pet.HitsMax
        return health < self.health_trigger / 100.0

    def loop(self):
        if self.gift_of_life:
            self.use_gift_of_life()

        if not self.check_health():
            Misc.Pause(self.DELAY)
            return

        if self.gift_of_renewal:
            # avoid using if pet is poisoned, use magery instead
            if self.pet.Poisoned:
                self.use_magery(cure_only=True)
            self.use_gift_of_renewal()

        if self.veterinary:
            self.use_bandages()

        if self.magery:
            self.use_magery()

        Misc.Pause(self.DELAY)

    def run(self):
        while True:
            Journal.Clear()

            if Player.IsGhost:
                Misc.Pause(self.DELAY)
                continue

            self.loop()


ph = PetHealing('pets', **settings)
ph.run()