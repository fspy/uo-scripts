# ez/_smith.py - Automated Blacksmithing Skill Training
from ez._trainer import TONGS_TYPE, run_craft_trainer

CONFIG = {
    "skill_name": "Blacksmithy",
    "tool_type": TONGS_TYPE,
    "salvage_tool_type": TONGS_TYPE,
    "target_skill": None,
    "brackets": [
        {
            "max_skill": 40.0,
            "page": None,
            "button": None,
            "desc": "too low - train to 40 in new haven",
        },
        {"max_skill": 75.0, "page": 22, "button": 44, "desc": "kryss"},
        {"max_skill": 89.9, "page": 22, "button": 107, "desc": "shuriken"},
        {"max_skill": 100.0, "page": 8, "button": 93, "desc": "circlet"},
        {"max_skill": 120.0, "page": 57, "button": 2, "desc": "boomerang"},
    ],
    "material_types": [0x1BF2],
    "material_threshold": 50,
    "storage_key": "ezSmith.Storage",
}


def main(target_skill=None):
    """Run Blacksmithy trainer with optional target skill.

    Args:
        target_skill: None for cap (unlimited), or float for specific target
    """
    config = CONFIG.copy()
    config["target_skill"] = target_skill
    run_craft_trainer(config)


if __name__ == "__main__":
    main()
