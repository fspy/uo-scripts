"""ez - Automated crafting trainer scripts package.

Trainers:
    - smith: Blacksmithy training
    - tailor: Tailoring training
    - tinker: Tinkering training
    - carpentry: Carpentry training
    - kegmaker: Multi-skill potion keg crafting

Launcher:
    - launcher: Gump-based trainer selection UI

Example:
    from ez._trainer import run_craft_trainer
    from ez._smith import main

    # Run a specific trainer
    main(target_skill=90.0)
"""

from ez._trainer import run_craft_trainer

__all__ = [
    "run_craft_trainer",
]
