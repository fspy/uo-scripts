# ezSmith - Automated Blacksmithing Skill Training

import API
from lib.crafting import run_craft_trainer, TONGS_TYPE

CONFIG = {
    'skill_name': 'Blacksmithy',
    'tool_type': 0x0FBB,  # tongs
    'salvage_tool_type': TONGS_TYPE,  # tongs for salvage
    'target_skill': 90.0,  # Set to None to train to skill cap
    'brackets': [
        {'max_skill': 40.0, 'page': None, 'button': None, 'desc': 'too low - train to 40 in new haven'},
        {'max_skill': 45.0, 'page': 43, 'button': 9, 'desc': 'mace'},
        {'max_skill': 50.0, 'page': 43, 'button': 16, 'desc': 'maul'},
        {'max_skill': 55.0, 'page': 22, 'button': 23, 'desc': 'cutlass'},
        {'max_skill': 59.5, 'page': 22, 'button': 37, 'desc': 'katana'},
        {'max_skill': 70.5, 'page': 22, 'button': 58, 'desc': 'scimitar'},
        {'max_skill': 106.4, 'page': 1, 'button': 65, 'desc': 'platemail gorget'},
        {'max_skill': 108.9, 'page': 1, 'button': 58, 'desc': 'platemail gloves'},
        {'max_skill': 116.3, 'page': 1, 'button': 51, 'desc': 'platemail arms'},
        {'max_skill': 118.8, 'page': 1, 'button': 72, 'desc': 'platemail legs'},
        {'max_skill': 120.0, 'page': 1, 'button': 79, 'desc': 'platemail tunics'},
    ],
}

run_craft_trainer(CONFIG)
