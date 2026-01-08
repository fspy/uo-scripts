# ez/_tailor.py - Automated Tailoring Skill Training
from ez._trainer import SCISSORS_TYPE, run_craft_trainer

CONFIG = {
    "skill_name": "Tailoring",
    "tool_type": 0xF9D,
    "salvage_tool_type": SCISSORS_TYPE,
    "target_skill": None,
    "brackets": [
        {
            "max_skill": 29.0,
            "page": None,
            "button": None,
            "desc": "too low - train manually to 29.0 first",
        },
        {"max_skill": 41.4, "page": 15, "button": 135, "desc": "short pants"},
        {"max_skill": 50.0, "page": 15, "button": 51, "desc": "cloak"},
        {"max_skill": 74.6, "page": 29, "button": 9, "desc": "fur boots"},
        {"max_skill": 100.0, "page": 22, "button": 86, "desc": "oil cloth"},
        {"max_skill": 120.0, "page": 43, "button": 9, "desc": "gargish cloth chest"},
    ],
    "material_types": [0x1766, 0x1767],
    "material_threshold": 50,
    "storage_key": "ezTailor.Storage",
}


def main(target_skill=None):
    """Run Tailoring trainer with optional target skill.

    Args:
        target_skill: None for cap (unlimited), or float for specific target
    """
    config = CONFIG.copy()
    config["target_skill"] = target_skill
    run_craft_trainer(config)


if __name__ == "__main__":
    main()
