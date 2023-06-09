import re

from AutoComplete import *

from lib.util import Hue

patterns = {
    r'concentration is disturbed': ('* FIZZLE *', Hue.Gray),
    r'attunement fades': ('- ATTUNEMENT -', Hue.Red),
    r'resists the effects of death ray': ('! DEATH RAY RESIST !', Hue.Yellow),
    r'honorable combat!': ('+ Honored +', Hue.Green),
    r'You are at peace.': ('+ Mana 100% +', Hue.Cyan),
    r'enter a meditative trance.': ('~ Meditating ~', Hue.Cyan),
    r'resists spell plague.': ('! Plague Resist !', Hue.Yellow),
    r'(\d+).+?absorbed.+?(\d+).+?shielding': (r'-\1 (\2)', Hue.Red),
    r'fallen beast, a special (reward|artifact)': ('++ Artifact! ++', Hue.Orange),
    r'notice the crest of minax on your fallen foe': ('++ Artifact! ++', Hue.Orange),
    r'respond immediately to the next blocked blow': ('^ Counter Attack ^', Hue.Orange),
    r'you feel that you might be able to': ('~ Evasion ~', Hue.Blue),
}

last_message = -1
while True:
    messages = [e for e in Journal.GetJournalEntry(last_message)]
    for message in messages:
        if message.Type != 'System':
            continue

        text = message.Text
        for pattern, (display, color) in patterns.items():
            match = re.search(pattern, text, re.U | re.IGNORECASE)
            if not match:
                continue

            if match.groups():
                display = re.sub(r'\\(\d+)',
                                 lambda m: match.group(int(m.group(1))),
                                 display)
            Player.HeadMessage(color, display)
    if messages:
        last_message = messages[-1].Timestamp
    Misc.Pause(50)
