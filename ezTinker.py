# ezTinker - Automated Tinkering Skill Training
from lib.crafting import run_craft_trainer

CONFIG = {
    "skill_name": "Tinkering",
    "tool_type": 0x1EB8,  # tinker tools
    "salvage_tool_type": None,  # No salvage for tinkering
    "target_skill": 70.1,  # Set to None to train to skill cap
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
    # Restock configuration
    "material_types": [0x1BF2],  # Iron ingots
    "material_threshold": 50,  # Restock when below this amount
    "storage_key": "ezTinker.Storage",  # Persistence key for storage container
}

run_craft_trainer(CONFIG)
