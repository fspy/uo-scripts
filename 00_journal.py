import re

import API
from _lib.utils import Hue, h, p


class JournalMonitor:
    def __init__(self):
        self._patterns = []
        self.last_timestamp = None

    def add_pattern(self, regex, display, hue):
        compiled = re.compile(regex, re.I)
        self._patterns.append((compiled, display, hue))

    def check_entry(self, entry):
        for compiled, display, hue in self._patterns:
            match = compiled.search(entry.Text)
            if not match:
                continue

            if match.lastindex:
                display = re.sub(
                    r"\\(\d+)",
                    lambda m: (
                        match.group(int(m.group(1)))
                        if int(m.group(1)) <= match.lastindex
                        else m.group(0)
                    ),
                    display,
                )

            return (display, hue)
        return None

    def run(self):
        while not API.StopRequested:
            entries = API.GetJournalEntries(2)
            if not entries:
                API.Pause(0.3)
                continue
            for entry in entries:
                if self.last_timestamp is None or entry.Time > self.last_timestamp:
                    match = self.check_entry(entry)
                    if match:
                        display, hue = match
                        h(display, API.Player, hue)
                    self.last_timestamp = entry.Time
            API.Pause(0.3)


patterns = {
    r"concentration is disturbed": ("* FIZZLE *", Hue.White),
    r"you regain your focus": ("! FOCUS !", Hue.Cyan),
    r"attunement fades": ("- ATTUNEMENT -", Hue.Red),
    r"resists the effects of death ray": ("! DEATH RAY RESIST !", Hue.Yellow),
    r"disturbs the focus necessary": ("! DEATH RAY INTERRUPT !", Hue.Yellow),
    r"honorable combat!": ("+ Honored +", Hue.Green),
    r"You are at peace.": ("+ Mana 100% +", Hue.Cyan),
    r"enter a meditative trance.": ("~ Meditating ~", Hue.Cyan),
    r"resists spell plague.": ("! Plague Resist !", Hue.Yellow),
    r"(\d+).+?absorbed.+?(\d+).+?shielding": (r"-\1 (\2)", Hue.Red),
    r"powerful magic, protecting": (r"Gift of Life", Hue.Green),
    r"fallen beast, a special (reward|artifact)": ("++ Artifact! ++", Hue.Magenta),
    r"notice the crest of minax on your fallen foe": ("++ Artifact! ++", Hue.Magenta),
    r"recover an artifact bearing the crest": ("++ Artifact! ++", Hue.Magenta),
    r"reward for slaying the mighty paragon": ("++ Artifact! ++", Hue.Magenta),
    r"the mark of demonic forces": ("++ Hyth Arti! ++", Hue.Red),
    r"notice the mark of an ice dragon": ("++ Artifact! ++", Hue.Cyan),
    r"respond immediately to the next blocked blow": ("^ Counter Attack ^", Hue.Orange),
    r"you feel that you might be able to": ("~ Evasion ~", Hue.Blue),
    r"the world will save": ("> World Save <", Hue.Blue),
}


monitor = JournalMonitor()
for regex, (display, hue) in patterns.items():
    monitor.add_pattern(regex, display, hue)

try:
    monitor.run()
except SystemError as _:
    p("JournalMonitor: interrupted", hue=Hue.Red)
