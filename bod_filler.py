# bod reader
from pprint import pprint
from AutoComplete import *
import re

bod_id = 0x2258
bod_colors = {
    'blacksmithing': 0x044e
}


def all_bods(kind):
    color = bod_colors[kind]
    bods_list = Items.FindAllByID(bod_id, color, Player.Backpack.Serial, 2)
    return bods_list


property_regex = {
    1045141: r'^All items must be exceptional\.$',
    1045142: r'^All items must be made with (?P<ingot_type>.+) ingots\.$',
    1060655: r'^large bulk order$',
    1060656: r'^amount to make: (?P<quantity>\d+)$',
    1060658: r'^(?P<item_type>.+): (?P<quantity>\d+)$',
    1060659: r'^(?P<item_type>.+): (?P<quantity>\d+)$',
    1060660: r'^(?P<item_type>.+): (?P<quantity>\d+)$',
    1060661: r'^(?P<item_type>.+): (?P<quantity>\d+)$',
    1060662: r'^(?P<item_type>.+): (?P<quantity>\d+)$',
    1060663: r'^(?P<item_type>.+): (?P<quantity>\d+)$',
}


class Bod:
    compiled_regex = {num: re.compile(regex)
                      for num, regex in property_regex.items()}

    def __init__(self, is_large, is_exceptional, ingot_type, total_quantity, item_quantities):
        self.is_large = is_large
        self.is_exceptional = is_exceptional
        self.ingot_type = ingot_type
        self.total_quantity = total_quantity
        self.item_quantities = item_quantities

    @classmethod
    def from_item(cls, item):
        properties = {prop.Number: prop.ToString() for prop in item.Properties}
        is_large = False
        is_exceptional = False
        ingot_type = 'iron'
        total_quantity = 0
        item_quantities = {}

        for num, regex in cls.compiled_regex.items():
            if num in properties:
                match = regex.match(properties[num])
                if match:
                    if num == 1060655:
                        is_large = True
                    elif num == 1045141:
                        is_exceptional = True
                    elif num == 1045142:
                        ingot_type = match.group('ingot_type')
                    elif num == 1060656:
                        total_quantity = int(match.group('quantity'))
                    elif num in [1060658, 1060659, 1060660, 1060661, 1060662, 1060663]:
                        item_type = match.group('item_type')
                        quantity = int(match.group('quantity'))
                        item_quantities[item_type] = quantity

        return cls(is_large, is_exceptional, ingot_type, total_quantity, item_quantities)

    def is_filled(self):
        return all(quantity == self.total_quantity for quantity in self.item_quantities.values())

    def missing_items(self):
        missing = {}
        if not self.is_filled():
            for item, quantity in self.item_quantities.items():
                if quantity < self.total_quantity:
                    missing[item] = self.total_quantity - quantity
        return missing


bods = [Bod.from_item(item) for item in all_bods('blacksmithing')]

for bod in bods:
    print(bod.missing_items())


with open('bodinfo.txt', 'w') as f:
    for bod in bods:
        pprint(vars(bod), f)
