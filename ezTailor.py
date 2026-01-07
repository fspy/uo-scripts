# ezTailor - Automated Tailoring Skill Training

from lib.crafting import SCISSORS_TYPE, run_craft_trainer

CONFIG = {
    "skill_name": "Tailoring",
    "tool_type": 0xF9D,  # sewing kit
    "salvage_tool_type": SCISSORS_TYPE,  # scissors for salvage
    "target_skill": None,  # Set to None to train to skill cap
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
    # Restock configuration
    "material_types": [0x1766, 0x1767],  # Cloth
    "material_threshold": 50,  # Restock when below this amount
    "storage_key": "ezTailor.Storage",  # Persistence key for storage container
}

run_craft_trainer(CONFIG)
