import time

import API
from _lib.utils import NOTORIETY_ENEMY, Hue, h


class Sampire:
    """Sampire combat script with timer-based defensive and onslaught logic."""

    # Configuration
    basher = True
    enemy_of_one = True
    divine_fury = False
    consecrate_weapon = True
    momentum_strike = True
    counter_attack = True
    evasion_threshold = 0.9
    confidence_threshold = False
    remove_curse = ("Blood Oath",)
    honor_targets = False
    onslaught = True
    trapped_box = 0x40358F00
    default_pause = 0.2
    MEGA_AGGRO = True

    # Cooldowns (seconds)
    EVASION_COOLDOWN = 20
    EVASION_DURATION = 8
    ONSLAUGHT_DEBUFF_DURATION = 6
    ONSLAUGHT_CAST_COOLDOWN = 6

    # Mana costs
    mana_costs = {
        "Enemy of One": 20,
        "Divine Fury": 10,
        "Consecrate Weapon": 10,
        "Momentum Strike": 10,
        "Counter Attack": 5,
        "Evasion": 10,
        "Confidence": 10,
        "Armor Ignore": 30,
        "Double Strike": 30,
        "Whirlwind Attack": 15,
        "Onslaught": 20,
        "Shield Bash": 35,
    }

    def __init__(self):
        """Initialize state timers and tracking."""
        self.evasion_cast_timer = 0
        self.onslaught_hit_timer = time.time()
        self.onslaught_cast_timer = 0
        self.apple_timer = time.time()
        self.honored_targets = []

    def run(self):
        """Main combat loop."""
        while not API.StopRequested:
            if API.Player.IsDead or API.Player.IsHidden:
                API.Pause(self.default_pause)
                continue

            enemies = self.get_enemies()
            if not enemies:
                API.Pause(self.default_pause)
                continue

            self.handle_status_effects()
            self.honor_target(enemies[0])

            if self.MEGA_AGGRO:
                self.aggro_all(enemies)

            self.combat_loop(enemies[0])

            if len(self.honored_targets) > 20:
                self.honored_targets = self.honored_targets[-20:]

    def get_enemies(self, max_distance=8):
        """Get list of hostile mobiles."""
        return API.NearestMobiles(NOTORIETY_ENEMY, max_distance)

    def handle_status_effects(self):
        """Handle trapped box and curse removal."""
        self.handle_paralyze()
        self.handle_curse()

    def handle_paralyze(self):
        """Use trapped box if paralyzed."""
        if not self.trapped_box:
            return

        if API.FindItem(self.trapped_box) and API.BuffExists("Paralyze"):
            API.UseObject(API.Found, True)
            API.Pause(self.default_pause)

    def handle_curse(self):
        """Remove curses with apples or spell."""
        if not self.remove_curse:
            return

        for curse in self.remove_curse:
            if not API.BuffExists(curse):
                continue

            if (
                API.FindType(0x2FD8, API.Backpack, hue=1160)
                and time.time() - self.apple_timer > 30
            ):
                API.UseObject(API.Found)
                return

            retries = 3
            while retries:
                API.CastSpell("Remove Curse")
                if API.WaitForTarget("beneficial"):
                    API.TargetSelf()
                    API.Pause(self.default_pause)
                retries -= 1

    def honor_target(self, enemy):
        """Honor target if enabled."""
        if not self.honor_targets or enemy.Serial in self.honored_targets:
            return

        API.Virtue("Honor")
        API.WaitForTarget(timeout=1)
        API.Target(enemy)  # pyright: ignore
        API.Pause(self.default_pause)

        if API.InJournalAny(["Honorable Combat", "cannot honor this monster"], True):
            self.honored_targets.append(enemy.Serial)

    def aggro_all(self, enemies):
        """Attack all enemies for MEGA_AGGRO mode."""
        for enemy in enemies:
            if enemy.Serial not in self.honored_targets:
                self.honored_targets.append(enemy.Serial)
                API.Attack(enemy)
                API.Pause(0.05)

    def combat_loop(self, focus):
        """Combat loop for a single target."""
        while API.FindMobile(focus) and focus.Distance < 2:
            self.handle_status_effects()
            self.apply_buffs()

            hp_ratio = API.Player.Hits / API.Player.HitsMax
            self.handle_defensives(hp_ratio)

            targets = len(self.get_enemies(1))
            abilities = list(API.CurrentAbilityNames())
            has_whirlwind = "Whirlwind Attack" in abilities
            has_double_strike = "Double Strike" in abilities
            has_armor_ignore = "ArmorIgnore" in abilities

            if targets > 2:
                self.handle_aoe(abilities, has_whirlwind)
            elif targets == 2:
                self.handle_momentum_strike()
            else:
                self.handle_single_target(
                    abilities, has_double_strike, has_armor_ignore
                )

            API.Attack(focus)
            API.Pause(self.default_pause)

        API.CancelTarget()

    def apply_buffs(self):
        """Apply combat buffs if not already active."""
        buffs = [
            ("Enemy of One", self.enemy_of_one, None),
            ("Divine Fury", self.divine_fury, None),
            ("Consecrate Weapon", self.consecrate_weapon, "Consecrate"),
        ]

        for spell_name, enabled, buff_name in buffs:
            buff_name = buff_name or spell_name
            if (
                enabled
                and not API.BuffExists(buff_name)
                and self.mana_check(spell_name)
            ):
                API.CastSpell(spell_name)
                API.Pause(self.default_pause)

    def handle_defensives(self, hp_ratio):
        """Cast defensive abilities based on health."""
        if self.basher:
            return

        active_defensives = ["Counter Attack", "Evasion", "Confidence"]
        if any(API.BuffExists(d) for d in active_defensives):
            return

        if (
            self.evasion_threshold
            and hp_ratio < self.evasion_threshold
            and time.time() - self.evasion_cast_timer >= self.EVASION_COOLDOWN
            and self.mana_check("Evasion")
        ):
            API.CastSpell("Evasion")
            self.evasion_cast_timer = time.time()
            return

        if (
            self.confidence_threshold
            and hp_ratio < self.confidence_threshold
            and self.mana_check("Confidence")
        ):
            API.CastSpell("Confidence")
            return

        if self.counter_attack and self.mana_check("Counter Attack"):
            API.CastSpell("Counter Attack")

    def handle_aoe(self, abilities, has_whirlwind):
        """Handle 3+ targets with Whirlwind or Momentum Strike."""
        if self.basher:
            self._toggle_ability(abilities, "Whirlwind Attack")
            return

        if has_whirlwind:
            if not API.SecondaryAbilityActive() and self.mana_check("Whirlwind Attack"):
                API.ToggleAbility("Secondary")
        elif (
            self.momentum_strike
            and not API.BuffExists("Momentum Strike")
            and self.mana_check("Momentum Strike")
        ):
            API.CastSpell("Momentum Strike")

    def handle_momentum_strike(self):
        """Handle 2 targets with Momentum Strike."""
        if self.basher:
            return

        if (
            self.momentum_strike
            and not API.BuffExists("Momentum Strike")
            and self.mana_check("Momentum Strike")
        ):
            API.CastSpell("Momentum Strike")

    def handle_single_target(self, abilities, has_double_strike, has_armor_ignore):
        """Handle single target combat with Onslaught and Double Strike."""
        if API.InJournal("deliver an onslaught of sword strikes"):
            self.onslaught_hit_timer = time.time()
            API.ClearJournal()

        if self.basher:
            if not API.BuffExists("Shield Bash") and self.mana_check("Shield Bash"):
                API.CastSpell("Shield Bash")
                return

            if API.BuffExists("Shield Bash"):
                self._toggle_ability(abilities, "ArmorIgnore")
            return

        if has_double_strike:
            debuff_active = (
                time.time() - self.onslaught_hit_timer <= self.ONSLAUGHT_DEBUFF_DURATION
            )

            if debuff_active:
                if not API.PrimaryAbilityActive() and self.mana_check("Double Strike"):
                    API.ToggleAbility("Primary")
            else:
                if (
                    self.onslaught
                    and time.time() - self.onslaught_cast_timer
                    >= self.ONSLAUGHT_CAST_COOLDOWN
                    and self.mana_check("Onslaught")
                ):
                    self.onslaught_cast_timer = time.time()
                    API.CastSpell("Onslaught")
        elif has_armor_ignore:
            if not API.PrimaryAbilityActive() and self.mana_check("Armor Ignore"):
                API.ToggleAbility("Primary")

    _SLOT = {0: "Primary", 1: "Secondary"}
    _CHECK = {0: API.PrimaryAbilityActive, 1: API.SecondaryAbilityActive}

    def _toggle_ability(self, abilities, ability_name):
        if ability_name not in abilities:
            return

        idx = abilities.index(ability_name)
        if not self._CHECK[idx]() and self.mana_check(ability_name):
            API.ToggleAbility(self._SLOT[idx])

    def mana_check(self, spell):
        """Check if player has enough mana for spell."""
        cost = self.mana_costs.get(spell, 0)
        return API.Player.Mana >= cost * (API.Player.LowerManaCost / 100.0)


# Run the script
try:
    h("Attack: Loaded!", hue=Hue.Green)
    sampire = Sampire()
    sampire.run()
except SystemError as _:
    h("Attack: Stopped", hue=Hue.Gray)
