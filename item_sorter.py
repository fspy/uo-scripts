# A nightmarish attempt to rank items based on their mods.
# Primarily focused on High Resists and Caster stats, but the weights are
# modifiable and can be used to find other types of mods.
# Untested with +Skill items, might need specialized regex for them.
# The library used (`ItemQuery`) can be find in `./lib/item_query.py`.

import re

from AutoComplete import *

from lib.item_query import ItemQuery
from lib.util import Hue, head_prompt

CONTAINER_WEAPON = 0x40722114
CONTAINER_UNRAVEL = 0x40722B66
CONTAINER_GARGOYLE = 0x402E19F0
CONTAINER_WEIGHTS = {
    0.35: 0x40316502,
    0.30: 0x4072208F,
    0.25: 0x40722B9C,
    0.20: 0x40722B88,
    0.15: 0x40722C94
}
weights = {
    # mod name (case insensitive): [weight, maximum value]
    'lower reagent cost': [4, 25],
    'lower mana cost': [6, 10],
    'mana regeneration': [5, 4],
    'mana increase': [3, 10],
    'intelligence bonus': [3, 10],
    'resist': [4, 35],
    'faster casting': [8, 4],
    'faster cast recovery': [10, 6]
}

melee_armor = re.compile(
    r'^((strength|dexterity) bonus|(hit point|stamina|mana) increase|'
    r'lower mana cost)', re.IGNORECASE)

melee_jewelry = re.compile(
    r'^(swing speed increase|((hit|defense) chance|damage) increase|'
    r'(strength|dexterity) bonus)', re.IGNORECASE)

caster_armor = re.compile(
    r'^(intelligence bonus|mana regeneration|mana increase|'
    r'lower (mana|reagent) cost)', re.IGNORECASE)

caster_jewelry = re.compile(
    r'^(intelligence bonus|mana regeneration|mana increase|'
    r'lower (mana|reagent) cost)|spell damage increase|'
    r'faster cast(ing| recovery)', re.IGNORECASE)


def find_gear(armor, jewelry, resists=0):
    q = ItemQuery(head_prompt('Where do I look?'))
    armor = q.count(*armor).amount(ItemQuery.Resist, resists)
    if armor.items: armor.move_all(Player.Backpack.Serial)
    jewelry = q.count(*jewelry)
    if jewelry.items: jewelry.move_all(Player.Backpack.Serial)


# find_gear((caster_armor, 4), (caster_jewelry, 5), 55)
find_gear((melee_armor, 4), (melee_jewelry, 4), 55)

# q = ItemQuery(source=head_prompt('Target source container'))
# q.move_all(q.query_prop(q.Gargoyle), CONTAINER_GARGOYLE)
# q.move_all(q.query_prop(q.Weapon), CONTAINER_WEAPON)
# q.move_all(q.query_prop(q.Unravel), CONTAINER_UNRAVEL)

# # convert to (weight, serial) tuples, ordered by highest weight
# weight_container = sorted(CONTAINER_WEIGHTS.items(),
#                           reverse=True,
#                           key=lambda x: x[0])

# for (weight, container) in weight_container:
#     q.move_all(q.query_weighted(float(weight), weights), container)

Misc.SendMessage("Done sorting items!", Hue.Cyan)
