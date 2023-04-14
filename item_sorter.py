# A nightmarish attempt to rank items based on their mods.
# Primarily focused on High Resists and Caster stats, but the weights are
# modifiable and can be used to find other types of mods.
# Untested with +Skill items, might need specialized regex for them.
# The library used (`ItemQuery`) can be find in `./lib/item_query.py`.

from lib.item_query import ItemQuery
from lib.util import head_prompt
from lib.colors import colors
from AutoComplete import *

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

q = ItemQuery(source=head_prompt('Target source container'))
q.move_all(q.query_prop(q.Unravel), CONTAINER_UNRAVEL)
q.move_all(q.query_prop(q.Gargoyle), CONTAINER_GARGOYLE)
q.move_all(q.query_prop(q.Weapon), CONTAINER_WEAPON)

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

# convert to (weight, serial) tuples, ordered by highest weight
weight_container = sorted(CONTAINER_WEIGHTS.items(),
                          reverse=True,
                          key=lambda x: x[0])

for (weight, container) in weight_container:
    q.move_all(q.query_weighted(float(weight), weights), container)

Misc.SendMessage("Done sorting items!", colors['cyan'])
