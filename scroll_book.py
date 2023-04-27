from collections import namedtuple
import os
from AutoComplete import *
from lib.util import Hue

csv = False
main_gump = 998728455
scrolls = []


def send_action(btn):
    Gumps.WaitForGump(main_gump, 2000)
    Gumps.SendAction(main_gump, btn)
    Gumps.WaitForGump(main_gump, 2000)


def parse_buttons(cutoff=100):
    data = Gumps.LastGumpRawData()
    return [
        int(line.split()[-2]) for line in data.split('{')
        if 'button' in line and int(line.split()[-2]) >= cutoff
    ]


def navigate(btn):
    send_action(btn)
    for n in parse_buttons():
        send_action(n)
        skill = Gumps.LastGumpGetLineList()[1:]
        Misc.SendMessage('Got skill {}...'.format(skill[0]), Hue.White)
        scrolls.append(Scroll._make(skill))
        send_action(1)
    send_action(2)


Scroll = namedtuple('Scroll',
                    ['Skill', 'Wondrous', 'Exalted', 'Mythical', 'Legendary'])

Misc.SendMessage('Waiting for you to open the book... (30s)', Hue.Cyan)
Gumps.WaitForGump(main_gump, 30000)
Misc.SendMessage('Okay, please wait for it to finish!', Hue.Magenta)

for section in parse_buttons(11):
    navigate(section)

Misc.SendMessage('Done looking at the book!', Hue.Green)
Gumps.CloseGump(main_gump)

file_name = f"scroll_data.{'csv' if csv else 'txt'}"
with open(file_name, 'w') as f:
    if csv:
        f.write('skill,120,115,110,105\n')
        for scroll in sorted(scrolls):
            f.write(f'{scroll.Skill},'
                    f'{scroll.Legendary},'
                    f'{scroll.Mythical},'
                    f'{scroll.Exalted},'
                    f'{scroll.Wondrous}\n')

    else:
        for scroll in sorted(scrolls):
            f.write(f'{scroll.Skill:<20}'
                    f'120: {scroll.Legendary:<5}'
                    f'115: {scroll.Mythical:<5}'
                    f'110: {scroll.Exalted:<5}'
                    f'105: {scroll.Wondrous}\n')

    f.close()
    Misc.SendMessage(rf'Wrote to file: "{os.getcwd()}\{file_name}"', Hue.Green)
