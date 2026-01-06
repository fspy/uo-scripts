# Legion Scripts for TazUO

Collection of Python scripts for the TazUO Ultima Online client using the Legion Scripting Engine.

## Crafting Trainers

Automated skill trainers that salvage crafted items to recover materials and restock from a storage container when low. Cleans up and returns materials when done.

| Script | Skill | Notes |
|--------|-------|-------|
| ezSmith.py | Blacksmithing | Uses tongs for salvage |
| ezTailor.py | Tailoring | Uses scissors for salvage |
| ezTinker.py | Tinkering | No salvage (consumes ingots) |

## Resource Gathering

| Script | Description |
|--------|-------------|
| Mining.py | Runebook mining bot with fire beetle smelting and auto-banking |
| Lumberjacking.py | Wandering lumberjack bot with beetle support |

## Utility Scripts

| Script | Description |
|--------|-------------|
| SmartHeal.py | Intelligent healing using Chivalry, Magery, or bandages |
| SpellTrainer.py | Spell skill trainer (Magery, Necromancy, Chivalry, Spellweaving) |
| tamer_helper.py | Pet monitoring - auto-cures poison, heals, maintains buffs |
| BODTracker.py | Tracks BOD timers across characters, auto-accepts BODs |
| SimpleLoom.py | Cloth production with spinning wheels and loom |

## Shared Libraries (lib/)

Common utilities used by multiple scripts:

- `crafting.py` - Gump navigation, salvage, restock logic
- `items.py` - Item manipulation helpers
- `persistence.py` - Save/load settings per character
- `runebook.py` - Runebook travel utilities
- `spells.py` - Spell timing calculations
- `journal.py` - Journal message parsing
- `weight.py` - Weight management
- `utils.py` - General utilities

## API.py

Type stubs for the Legion Scripting API. Provides autocomplete and type hints for IDE integration. Auto-generated, do not edit.

## Requirements

- [TazUO Client](https://github.com/bittiez/TazUO)
- Legion Scripting Engine (included with TazUO)

## References

- [TazUO Documentation](https://github.com/bittiez/TazUO/wiki)
- [Public Legion Scripts](https://github.com/PlayTazUO/PublicLegionScripts)
