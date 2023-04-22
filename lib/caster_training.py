"""Trains caster-type skills automatically.

This scripts allows you to configure spells, their costs and targets, and at 
which point they start being used while training the specified skill.

Done as "wanted to see if I could", this is very much a work in progress.
Currently missing a few guardrails but shouldn't break much.

Example usage:

    # heal yourself
    gheal = Spell('Greater Heal', 24, Player.Serial)
    gheal.cast()

    # cast flamestrike on yourself, but make sure to keep health high
    # using the spell assigned previously in `gheal`.
    safe_fs = SpellSafe('Flamestrike', 50, Player.Serial, gheal)
    safe_fs.cast()

    # defines a table where the key is the highest skill point where it
    # will be cast. in this case, uses `gheal` until 35, then uses 
    # `safe_fs`, stopping at 70. "until key, cast value."
    skill_table = {
        35: gheal,
        70: safe_fs,
    }

    # defines what skill to check for gains, providing a table to determine
    # when to switch spells according to current skill value.
    ct = CasterTraining('Magery', skill_table)
    ct.run()
"""

from AutoComplete import *
from decimal import *


class Spell:
    """Representation of a Spell.

    Handles mana costs, cast speed and recovery of a spell.
    Currently doesn't consider cast time of spells without a target.
    For skills where FC can go above 2, only considers up to 2.

    Attributes:
        spell_name: The spell's name, same as in-game.
        mana_cost: Raw mana cost of the spell. LMC is calculated on creation.
        target: A target serial. `Player.Serial` for self-cast.
                If `None`, doesn't process targetting.

    """

    def __init__(self, spell_name, mana_cost, target=None):
        """Initializes a spell instance, taking into account the player's LMC.

        Args:
            spell_name: sets the spell name.
            mana_cost: sets the spell mana cost.
            target: if present, sets the target's serial
        """
        self.spell_name = spell_name
        self.mana_cost = int(mana_cost * (1 - Player.LowerManaCost / 100))
        self.target = target

    def cast(self):
        """Casts the instantiated spell.

        Checks if a target exists, then handles it.
        Pauses are calculated according to player's FC and FCR stats.
        """
        Spells.Cast(self.spell_name)
        if self.target:
            Target.WaitForTarget(2000, False)
            Target.TargetExecute(self.target)
        else:
            # faster casting (prob should check skills that use 4 fc)
            Misc.Pause(2000 - int(Player.FasterCasting / 4 * 1000))

        # faster cast recovery - (cap - players) / 250ms
        fcr = int((6 - Player.FasterCastRecovery) / 4 * 1000)
        Misc.Pause(fcr + 50)


class SpellSafe(Spell):
    """A potentially harmful spell, that requires health monitoring.

    Sometimes a spell used damages the player, so there needs to be a way to
    make sure the player's health stays high. This is solved by passing in
    another `Spell` that is cast on low health.

    See `Spell`.
    """

    def __init__(self, spell_name, mana_cost, target, safe_spell):
        super().__init__(spell_name, mana_cost, target)
        self.safe_spell = safe_spell

    def cast(self):
        """Casts the spell, safely.

        This is done by checking if the player is missing health, and if so,
        casting the stored "safe spell" before the actual skill-gaining spell.
        """
        if Player.Hits < Player.HitsMax / 2:
            while Player.Hits < Player.HitsMax:
                self.safe_spell.cast()
                Misc.Pause(50)
        super().cast()


class CasterTraining:
    """Trains caster-like skills, using a spells table to decide what to cast.

    Attributes:
        skill_name: The name of the skill being trained.
        skill_cap: The maximum skill possible for the character.
        spell_table: A dictionary of skill values to spells.
        skill_ranges: A sorted list of the table's skill values.
    """

    def __init__(self, skill_name, spell_table):
        """Initializes an instance using the skill's name and spell tables.

        The player's skill cap is set here because it is unlikely to change
        during training. Also avoids reading game data every loop.

        There is a conversion to Decimal on the keys of `spell_table` to avoid
        floating point arithmetic errors with the current skill value later.

        Args:
            skill_name: Defines the skill being trained.
            spell_table: Defines a table of skill values and spells to be cast.
        """
        self.skill_name = skill_name
        self.skill_cap = Player.GetSkillCap(skill_name)
        self.spell_table = {
            Decimal(a).quantize(Decimal("0.1")): b
            for a, b in spell_table.items()
        }
        self.skill_ranges = sorted(self.spell_table.keys())

    def check_mana(self, cost):
        """Ensures that the player has enough mana to cast the selected spell.

        If it is not possible to cast it, uses the Meditation skill to reach
        maximum mana. This function waits until full and retries on failure.

        Args:
            cost: the mana cost of the spell.
        """
        if Player.Mana >= cost:
            return

        Player.UseSkill("Meditation")
        while Player.Mana < Player.ManaMax:
            if not Player.BuffsExist("Meditation") and not Timer.Check("med"):
                Player.UseSkill("Meditation")
                Timer.Create("med", 10500)
            Misc.Pause(100)

    def get_spell(self, skill_value):
        """Retrieves a spell from the table based on skill value.

        Searches the skill table for a spell matching the player's skill.
        Returns the first value if none are suitable.

        Args:
            skill_value: The player's current skill value.

        Returns:
            The matching `Spell` object according to skill value.
        """
        skill = Decimal(skill_value).quantize(Decimal(".1"))
        skill_range = self.skill_ranges[0]
        for k in self.skill_ranges:
            if k > skill:
                skill_range = k
                break
        return self.spell_table[skill_range]

    def run(self):
        """Runs the main loop where spells are cast.

        Casts the selected spells until the skill's value reaches maximum.
        In case of no spell being found, (probably) due to an invalid spell
        table, a message is sent to the client.
        Halts if the player is dead.

        """
        while (not Player.IsGhost
               and Player.GetRealSkillValue(self.skill_name) < self.skill_cap):
            spell = self.get_spell(Player.GetSkillValue(self.skill_name))
            if not spell:
                Misc.SendMessage("spell not found")
                break
            self.check_mana(spell.mana_cost)
            spell.cast()
            Misc.Pause(200)  # don't freak out


"""
Class Presets
Pre-configured per-spell, for easier importing/running.
"""


class ChivalryTrainer(CasterTraining):
    skill_name = 'Chivalry'
    spell_table = {
        45: Spell('Consecrate Weapon', 10),
        60: Spell('Divine Fury', 15),
        70: Spell('Enemy of One', 20),
        90: Spell('Holy Light', 10),
        120: Spell('Noble Sacrifice', 20),
    }

    def __init__(self):
        super().__init__(self.skill_name, self.spell_table)


class MageryTrainer(CasterTraining):
    _heal = Spell('heal', 4, Player.Serial)
    skill_name = 'Magery'
    spell_table = {
        45: SpellSafe('Fireball', 9, Player.Serial, _heal),
        55: SpellSafe('Lightning', 11, Player.Serial, _heal),
        65: Spell('Magic Reflection', 14, Player.Serial),
        75: Spell('Reveal', 20, Player.Serial),
        90: SpellSafe('Flamestrike', 40, Player.Serial, _heal),
        120: Spell('Earthquake', 50)
    }

    def __init__(self):
        super().__init__(MageryTrainer.skill_name, MageryTrainer.spell_table)


class MysticismTrainer(CasterTraining):
    _heal = Spell('heal', 4, Player.Serial)
    skill_name = 'Mysticism'
    spell_table = {
        40: SpellSafe('Eagle Strike', 9, Player.Serial, _heal),
        62.9: Spell('Stone Form', 11),
        80: Spell('Cleansing Winds', 20, Player.Serial),
        95: Spell('Hail Storm', 50, Player.Serial),
        120: Spell('Nether Cyclone', 50, Player.Serial),
    }

    def __init__(self):
        super().__init__(self.skill_name, self.spell_table)


class NecromancyTrainer(CasterTraining):
    skill_name = 'Necromancy'
    spell_table = {
        50:
        SpellSafe('Pain Spike', 5, Player.Serial,
                  Spell('Heal', 4, Player.Serial)),
        70:
        Spell('Horrific Beast', 11),
        90:
        Spell('Wither', 23),
        100:
        Spell('Lich Form', 25),
        120:
        Spell('Vampiric Embrace', 25),
    }

    def __init__(self):
        super().__init__(self.skill_name, self.spell_table)


class SpellweavingTrainer(CasterTraining):
    _heal = Spell('heal', 4, Player.Serial)
    skill_name = 'Spellweaving'
    spell_table = {
        20: Spell('Arcane Circle', 24),
        33: Spell('Immolating Weapon', 32),
        58: Spell('Reaper Form', 34),
        74: Spell('Essence of Wind', 40),
        90: Spell('Wildfire', 50, Player.Serial),
        120: SpellSafe('Word of Death', 50, Player.Serial, _heal)
    }

    def __init__(self):
        super().__init__(self.skill_name, self.spell_table)
