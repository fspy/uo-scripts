# ezSmith - Automated Blacksmithing Skill Training
from lib.crafting import TONGS_TYPE, run_craft_trainer

CONFIG = {
    "skill_name": "Blacksmithy",
    "tool_type": TONGS_TYPE,  # tongs
    "salvage_tool_type": TONGS_TYPE,  # tongs for salvage
    "target_skill": None,  # Set to None to train to skill cap
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
    # Restock configuration
    "material_types": [0x1BF2],  # Iron ingots
    "material_threshold": 50,  # Restock when below this amount
    "storage_key": "ezSmith.Storage",  # Persistence key for storage container
}

run_craft_trainer(CONFIG)
