# ezTailor - Automated Tailoring Skill Training

import API
from lib.crafting import run_craft_trainer, SCISSORS_TYPE

CONFIG = {
    "skill_name": "Tailoring",
    "tool_type": 0xF9D,  # sewing kit
    "salvage_tool_type": SCISSORS_TYPE,  # scissors for salvage
    "target_skill": 96.0,  # Set to None to train to skill cap
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
        {"max_skill": 120.0, "page": 22, "button": 86, "desc": "oil cloth"},
    ],
}

run_craft_trainer(CONFIG)
