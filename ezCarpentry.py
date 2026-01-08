# ezCarpentry - Automated Carpentry Skill Training
from lib.crafting import run_craft_trainer

CONFIG = {
    "skill_name": "Carpentry",
    "tool_type": 0x1034,  # saw (updated graphic)
    "salvage_tool_type": None,  # carpentry items can't be salvaged
    "target_skill": 100.0,
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
        {"max_skill": 96.0, "page": 22, "button": 107, "desc": "black staff"},
        {"max_skill": 100.0, "page": 22, "button": 44, "desc": "wild staff"},
    ],
    # Restock configuration
    "material_types": [0x1BD7],  # Boards
    "material_threshold": 50,  # Restock when below this amount
    "storage_key": "ezCarpentry.Storage",  # Persistence key for storage container
    # Trash configuration (most carpentry items can't be axe-destroyed)
    "trash_container_key": "ezCarpentry.Trash",  # Persistence key for trash barrel
    "trash_item_types": [
        0x0E3D,  # large crate
        0x0E3E,  # medium crate
        0x0E3F,  # small? crate
        0x1B7A,  # wooden shield
        0x27AA,  # fukiya (guessing - will discover)
        0x0E89,  # quarter staff
        0x13F8,  # gnarled staff
        0x0DF0,  # black staff
        0x2D25,  # wild staff (guessing - will discover)
        # Add more item graphics as discovered
    ],
}

run_craft_trainer(CONFIG)
