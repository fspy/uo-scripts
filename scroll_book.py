import os
from AutoComplete import *
from lib.util import Hue

main_gump = 998728455
scrolls = {}


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
        scrolls[skill[0]] = [int(n) for n in skill[1:]]
        send_action(1)
    send_action(2)


Misc.SendMessage('Waiting for you to open the book... (30s)', Hue.Cyan)
Gumps.WaitForGump(main_gump, 30000)
Misc.SendMessage('Okay, please wait for it to finish!', Hue.Magenta)

for section in parse_buttons(11):
    navigate(section)

Misc.SendMessage('Done looking at the book!', Hue.Green)
Gumps.CloseGump(main_gump)

with open('scroll_data.txt', 'w') as f:
    tpl = '{:<20} 120: {:<5} 115: {:<5} 110: {:<5} 105: {:<5}\n'
    for skill, (five, ten, fifteen, twenty) in sorted(scrolls.items()):
        f.write(tpl.format(skill, twenty, fifteen, ten, five))

    f.close()
    Misc.SendMessage(
        'Wrote to file: "{}\\scroll_data.txt"'.format(os.getcwd()), Hue.Green)
