from AutoComplete import *

from lib.util import head_prompt

TAILORING_DATA = {
    'Leather': {
        # amount: [small, 4 part, 5 part, 6 part]
        10: [10, 310, 510, 610],
        15: [25, 325, 525, 625],
        20: [50, 350, 550, 650]
    },
    'Spined': {
        10: [60, 360, 460, 560],
        15: [75, 375, 475, 575],
        20: [100, 400, 500, 600]
    },
    'Horned': {
        10: [110, 410, 510, 610],
        15: [125, 425, 525, 625],
        20: [150, 450, 550, 650]
    },
    'Barbed': {
        10: [160, 460, 560, 660],
        15: [175, 475, 575, 675],
        20: [200, 500, 600, 700]
    }
}

PROP_EXCEPTIONAL = 0xff295
PROP_AMOUNT = 0x102f30
PROP_MATERIAL_START = 0x100304
PROP_MATERIAL_END = 0x100306
PROP_SMALL = 0x102f2e
PROP_LARGE_START = 0x102f32
PROP_LARGE_END = 0x102f37

materials = {
    0x100304: 'Spined',
    0x100305: 'Horned',
    0x100306: 'Barbed',
}


def bod_value(item):
    exceptional = False
    amount = 0
    material = 'Leather'
    small = False
    part_idx = 0

    for prop in item.Properties:

        if prop.Number == PROP_EXCEPTIONAL:
            exceptional = True

        elif prop.Number == PROP_AMOUNT:
            amount = int(f'{prop}'.split(':')[-1])

        elif PROP_MATERIAL_START <= prop.Number <= PROP_MATERIAL_END:
            material = materials[prop.Number]

        elif prop.Number == PROP_SMALL:
            small = True

        elif PROP_LARGE_START <= prop.Number <= PROP_LARGE_END:
            part_idx = max(part_idx, prop.Number - PROP_LARGE_START)

    if not small: part_idx -= 3
    value = TAILORING_DATA[material][amount][part_idx]
    if exceptional and value is not None: value += 100

    return value


try:
    item = Items.FindBySerial(head_prompt('Click a BOD'))
    parsed = bod_value(item)
    Player.HeadMessage(1153, f'The selected BOD is worth {parsed} points.')
except Exception as e:
    print('Error: Invalid BOD or user cancelled prompt.')
    print(e)
