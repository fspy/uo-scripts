# ez/_tinker.py - Automated Tinkering Skill Training
from ez._trainer import run_craft_trainer

CONFIG = {
    "skill_name": "Tinkering",
    "tool_type": 0x1EB8,
    "salvage_tool_type": None,
    "target_skill": None,
    "brackets": [
        {
            "max_skill": 40.0,
            "page": None,
            "button": None,
            "desc": "too low - train to 40 in new haven",
        },
        {"max_skill": 45.0, "page": 15, "button": 2, "desc": "scissors"},
        {"max_skill": 60.0, "page": 15, "button": 86, "desc": "tongs"},
        {"max_skill": 75.0, "page": 15, "button": 121, "desc": "lockpick"},
        {"max_skill": 85.0, "page": 1, "button": 9, "desc": "bracelet"},
        {"max_skill": 90.0, "page": 36, "button": 37, "desc": "spyglass"},
        {"max_skill": 100.0, "page": 1, "button": 2, "desc": "ring"},
    ],
    "material_types": [0x1BF2],
    "material_threshold": 50,
    "storage_key": "ezTinker.Storage",
}


def main(target_skill=None):
    """Run Tinkering trainer with optional target skill.

    Args:
        target_skill: None for cap (unlimited), or float for specific target
    """
    config = CONFIG.copy()
    config["target_skill"] = target_skill
    run_craft_trainer(config)


if __name__ == "__main__":
    main()
