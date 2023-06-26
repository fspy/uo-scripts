# A nightmarish attempt to rank items based on their mods.
# Primarily focused on High Resists and Caster stats, but the weights are
# modifiable and can be used to find other types of mods.
# Untested with +Skill items, might need specialized regex for them.
# The library used (`ItemQuery`) can be find in `./lib/item_query.py`.

import re

from AutoComplete import *

from lib.item_query import ItemQuery
from lib.util import Hue, head_prompt


def find_gear(source, destination=Player.Backpack.Serial, settings={}):
    q = ItemQuery(source)
    if settings.get('resist'):
        Misc.SendMessage('Moving high resist items...')
        items = q.amount(ItemQuery.Resist, settings['resist'])
        items.move_all(destination)

    # if settings.get('skill'):
    #     Misc.SendMessage('Moving high skill items...')
    #     items = q.amount(ItemQuery.Skill, settings['skill'])
    #     items.move_all(destination)

    if settings.get('caster'):
        Misc.SendMessage('Moving caster armor...')
        items = q.count(caster_armor, settings['caster'])
        items = items.amount(ItemQuery.Resist, 60)
        items.move_all(destination)

    if settings.get('casterjewelry'):
        Misc.SendMessage('Moving caster jewelry...')
        items = q.count(caster_jewelry, settings['casterjewelry'])
        items.move_all(destination)

    if settings.get('fighter'):
        Misc.SendMessage('Moving fighter armor...')
        items = q.count(fighter_armor, settings['fighter'])
        items = items.amount(ItemQuery.Resist, 60)
        items.move_all(destination)

    if settings.get('fighterjewelry'):
        Misc.SendMessage('Moving fighter jewelry...')
        items = q.count(fighter_jewelry, settings['fighterjewelry'])
        items.move_all(destination)


fighter_armor = re.compile(
    r'^((strength|dexterity) bonus|(hit point|stamina|mana) increase|'
    r'lower mana cost)', re.IGNORECASE)

fighter_jewelry = re.compile(
    r'^((swing speed|damage|mana|stamina|(hit|defense) chance) increase|'
    r'(strength|dexterity) bonus)', re.IGNORECASE)

caster_armor = re.compile(
    r'^(intelligence bonus|mana regeneration|mana increase|'
    r'lower (mana|reagent) cost)', re.IGNORECASE)

caster_jewelry = re.compile(
    r'^(intelligence bonus|mana regeneration|mana increase|'
    r'lower (mana|reagent) cost)|spell damage increase|'
    r'faster cast(ing| recovery)', re.IGNORECASE)

settings = {
    'resist': 80,
    'skill': 45,
    'caster': 4,
    'fighter': 5,
    'casterjewelry': 5,
    'fighterjewelry': 5
}

src = head_prompt('Target container to sort')
dst = head_prompt('Target where to put items')
find_gear(src, dst, settings)

Misc.SendMessage("Done sorting items!", Hue.Cyan)
