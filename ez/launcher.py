# ez/launcher.py - Gump-based trainer selection UI
"""
Trainer Launcher Gump

UI Layout:
┌─────────────────────────────────────────┐
│  ez Trainer                          [X]│
├─────────────────────────────────────────┤
│  Trainer:  [Blacksmithy      ▼]         │
│  Target:   [____90.0_____] [Cap]        │
│  Current:  Blacksmithy: 45.0 / 100.0    │
│                                         │
│           [         TRAIN         ]     │
│                                         │
└─────────────────────────────────────────┘

Features:
- Dropdown to select trainer
- Editbox for target skill value
- Cap button (sets target to None for unlimited training)
- Shows current skill value for selected trainer
- Train button launches selected trainer
"""

import API

try:
    import ez._smith
    import ez._tailor
    import ez._tinker
    import ez._carpentry
    import ez._kegmaker
except ImportError:
    pass

TRAINERS = [
    {"name": "Blacksmithy", "module": "ez._smith", "skill": "Blacksmithy"},
    {"name": "Tailoring", "module": "ez._tailor", "skill": "Tailoring"},
    {"name": "Tinkering", "module": "ez._tinker", "skill": "Tinkering"},
    {"name": "Carpentry", "module": "ez._carpentry", "skill": "Carpentry"},
    {"name": "KegMaker", "module": "ez._kegmaker", "skill": None},
]

GUMP_WIDTH = 320
GUMP_HEIGHT = 180
DROPDOWN_WIDTH = 200
EDITBOX_WIDTH = 80
BUTTON_WIDTH = 60
TRAIN_BUTTON_WIDTH = 200
TRAIN_BUTTON_HEIGHT = 35
HUE_SUCCESS = 68
HUE_INFO = 33
HUE_ALERT = 32


class TrainerLauncherGump:
    def __init__(self):
        self.gump = None
        self.dropdown = None
        self.editbox = None
        self.cap_btn = None
        self.train_btn = None
        self.close_btn = None
        self.skill_label = None

    def create(self):
        self.gump = API.CreateGump(True, True, False)
        self.gump.SetWidth(GUMP_WIDTH)
        self.gump.SetHeight(GUMP_HEIGHT)
        self.gump.CenterXInViewPort()
        self.gump.CenterYInViewPort()

        bg = API.CreateGumpColorBox(0.9, "#1a1a1a")
        bg.SetWidth(GUMP_WIDTH)
        bg.SetHeight(GUMP_HEIGHT)
        self.gump.Add(bg)

        title = API.CreateGumpTTFLabel("ez Trainer", 22, "#FFFFFF", "IBMPlexSans-Text")
        title.SetX(10)
        title.SetY(10)
        self.gump.Add(title)

        trainer_names = [t["name"] for t in TRAINERS]
        self.dropdown = API.Gumps.CreateDropDown(DROPDOWN_WIDTH, trainer_names, 0)
        self.dropdown.SetX(10)
        self.dropdown.SetY(45)
        self.gump.Add(self.dropdown)

        def on_selection_changed(index):
            self._update_skill_display()

        self.dropdown.OnDropDownOptionSelected(on_selection_changed)

        self.editbox = API.CreateGumpTextBox("90.0", EDITBOX_WIDTH, 25, False)
        self.editbox.SetX(10)
        self.editbox.SetY(75)
        self.gump.Add(self.editbox)

        self.cap_btn = API.CreateSimpleButton("Cap", BUTTON_WIDTH, 25)
        self.cap_btn.SetX(10 + EDITBOX_WIDTH + 5)
        self.cap_btn.SetY(75)
        self.gump.Add(self.cap_btn)

        self.skill_label = API.CreateGumpTTFLabel("", 16, "#808080", "IBMPlexSans-Text")
        self.skill_label.SetX(10)
        self.skill_label.SetY(105)
        self.gump.Add(self.skill_label)

        self.train_btn = API.CreateSimpleButton(
            "TRAIN", TRAIN_BUTTON_WIDTH, TRAIN_BUTTON_HEIGHT
        )
        self.train_btn.SetX((GUMP_WIDTH - TRAIN_BUTTON_WIDTH) // 2)
        self.train_btn.SetY(130)
        self.gump.Add(self.train_btn)

        self.close_btn = API.CreateSimpleButton("X", 30, 25)
        self.close_btn.SetX(GUMP_WIDTH - 40)
        self.close_btn.SetY(10)
        self.gump.Add(self.close_btn)

        self._update_skill_display()
        API.Gumps.AddGump(self.gump)

    def _update_skill_display(self):
        idx = self.dropdown.GetSelectedIndex()
        trainer = TRAINERS[idx]

        if trainer["skill"] is None:
            self.skill_label.SetText("KegMaker - Multi-skill crafting")
        else:
            try:
                skill = API.GetSkill(trainer["skill"])
                current = skill.Value if skill else 0
                cap = skill.Cap if skill else 100
                self.skill_label.SetText(f"{trainer['skill']}: {current:.1f} / {cap}")
            except Exception:
                self.skill_label.SetText(f"{trainer['skill']}: --")

    def _get_target_skill(self):
        text = self.editbox.GetText()
        if not text or text.strip() == "":
            return None
        try:
            return float(text)
        except ValueError:
            return None

    def _run_trainer(self):
        idx = self.dropdown.GetSelectedIndex()
        trainer = TRAINERS[idx]
        target_skill = self._get_target_skill()

        self.dispose()

        try:
            if trainer["skill"] is None:
                getattr(ez._kegmaker, "main")()
            else:
                getattr(
                    ez._smith
                    if "smith" in trainer["module"]
                    else ez._tailor
                    if "tailor" in trainer["module"]
                    else ez._tinker
                    if "tinker" in trainer["module"]
                    else ez._carpentry,
                    "main",
                )(target_skill)
        except Exception as e:
            API.SysMsg(f"Error running {trainer['name']}: {e}", HUE_ALERT)

    def dispose(self):
        if self.gump:
            try:
                self.gump.Dispose()
            except Exception:
                pass
            self.gump = None


def main():
    launcher = TrainerLauncherGump()
    launcher.create()

    while not API.StopRequested:
        API.ProcessCallbacks()

        if launcher.close_btn.HasBeenClicked():
            launcher.dispose()
            break

        if launcher.cap_btn.HasBeenClicked():
            launcher.editbox.SetText("")

        if launcher.train_btn.HasBeenClicked():
            launcher._run_trainer()
            launcher.create()
            continue

        API.Pause(0.1)

    launcher.dispose()


if __name__ == "__main__":
    main()
