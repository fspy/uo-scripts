# ez/_carpentry.py - Automated Carpentry Skill Training
from ez._trainer import run_craft_trainer

CONFIG = {
    "skill_name": "Carpentry",
    "tool_type": 0x1034,
    "salvage_tool_type": None,
    "target_skill": None,
    "brackets": [
        {
            "max_skill": 30.0,
            "page": None,
            "button": None,
            "desc": "too low - train at NPC to 30.0 first",
        },
        {"max_skill": 48.0, "page": 15, "button": 16, "desc": "medium crate"},
        {"max_skill": 53.0, "page": 15, "button": 23, "desc": "large crate"},
        {"max_skill": 60.0, "page": 29, "button": 2, "desc": "wooden shield"},
        {"max_skill": 74.0, "page": 22, "button": 30, "desc": "fukiya"},
        {"max_skill": 79.0, "page": 22, "button": 9, "desc": "quarter staff"},
        {"max_skill": 82.0, "page": 22, "button": 16, "desc": "gnarled staff"},
        {"max_skill": 106.5, "page": 22, "button": 107, "desc": "black staff"},
        {"max_skill": 113.8, "page": 22, "button": 44, "desc": "wild staff"},
    ],
    "material_types": [0x1BD7],
    "material_threshold": 50,
    "storage_key": "ezCarpentry.Storage",
    "trash_container_key": "ezCarpentry.Trash",
    "trash_item_types": [
        0x0E3D,
        0x0E3E,
        0x0E3F,
        0x1B7A,
        0x27AA,
        0x0E89,
        0x13F8,
        0x0DF0,
        0x2D25,
    ],
}


def main(target_skill=None):
    """Run Carpentry trainer with optional target skill.

    Args:
        target_skill: None for cap (unlimited), or float for specific target
    """
    config = CONFIG.copy()
    config["target_skill"] = target_skill
    run_craft_trainer(config)


if __name__ == "__main__":
    main()
