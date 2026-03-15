import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import API

RUNEBOOK_GRAPHIC = 0x22C5
RUNEBOOK_GUMP_ID = 0x59

RECALL_BUTTON_BASE = 50
RECALL_BUTTON_STRIDE = 1

SJ_BUTTON_BASE = 6
SJ_BUTTON_STRIDE = 6

TRAVEL_FAIL_MSGS = [
    "you have not yet recovered",
    "spell fizzles",
    "concentration is disturbed",
    "target is blocked",
]


class Runebook:
    def __init__(self, serial: int):
        self.serial = serial

    def open(self, timeout: float = 2.0) -> bool:
        API.UseObject(self.serial)
        return API.WaitForGump(RUNEBOOK_GUMP_ID, timeout)

    def recall_to_index(self, index: int) -> bool:
        if index < 0 or index > 15:
            API.SysMsg(f"Invalid rune index: {index}", 32)
            return False

        if not API.HasGump(RUNEBOOK_GUMP_ID):
            if not self.open():
                API.SysMsg("Failed to open runebook", 32)
                return False

        button_id = RECALL_BUTTON_BASE + (index * RECALL_BUTTON_STRIDE)
        result = API.ReplyGump(button_id, RUNEBOOK_GUMP_ID)
        API.Pause(0.5)
        return result

    def sacred_journey_to_index(self, index: int) -> bool:
        if index < 0 or index > 15:
            API.SysMsg(f"Invalid rune index: {index}", 32)
            return False

        if not API.HasGump(RUNEBOOK_GUMP_ID):
            if not self.open():
                API.SysMsg("Failed to open runebook", 32)
                return False

        button_id = SJ_BUTTON_BASE + (index * SJ_BUTTON_STRIDE)
        result = API.ReplyGump(button_id, RUNEBOOK_GUMP_ID)
        API.Pause(0.5)
        return result


def wait_for_travel(timeout: float = 5.0) -> bool:
    """Wait for travel to complete. Returns True if position changed."""
    start_pos = (API.Player.X, API.Player.Y)
    deadline = time.time() + timeout

    while time.time() < deadline and not API.StopRequested:
        if API.InJournalAny(TRAVEL_FAIL_MSGS):
            return False

        if abs(API.Player.X - start_pos[0]) > 5 or abs(API.Player.Y - start_pos[1]) > 5:
            return True

        API.Pause(0.1)

    return False


def recall_and_target(target_serial: int, use_sacred_journey: bool = False) -> bool:
    """Cast Recall/Sacred Journey and target an item. Returns True if travel succeeded."""
    spell = "Sacred Journey" if use_sacred_journey else "Recall"

    API.ClearJournal()
    API.CastSpell(spell)

    if not API.WaitForTarget(timeout=5):
        API.SysMsg(f"{spell} failed - no target cursor", 32)
        return False

    API.Target(target_serial)  # type: ignore
    return wait_for_travel()


def recall_with_retry(
    target_serial: int,
    max_retries: int = 3,
    retry_delay: float = 2.0,
    use_sacred_journey: bool = False,
) -> bool:
    """Recall with automatic retry on failure."""
    for attempt in range(1, max_retries + 1):
        API.ClearJournal()
        if recall_and_target(target_serial, use_sacred_journey):
            return True
        if attempt < max_retries:
            API.Pause(retry_delay)
    return False


def show_runebook_runes(rb_serial=None):
    """Display a gump with buttons for each rune in a runebook."""
    if rb_serial is None:
        API.SysMsg("Target the runebook", 946)
        rb_serial = API.RequestTarget()
        if not rb_serial:
            API.SysMsg("No target selected", 33)
            return

    def open_runebook(timeout=2.0):
        if not API.HasGump(0x59):
            API.UseObject(rb_serial, True)
            start = time.time()
            while not API.HasGump(0x59) and time.time() - start < timeout:
                API.Pause(0.1)
        return API.HasGump(0x59)

    clicked_rune = [None]

    def make_callback(rune_index):
        def callback():
            clicked_rune[0] = rune_index

        return callback

    if not open_runebook():
        API.SysMsg("Failed to open runebook gump", 33)
        return

    gump_content = API.GetGumpContents(0x59)
    num_runes = gump_content.count("default")

    if num_runes == 0:
        API.SysMsg("No runes found in runebook", 33)
        return

    API.SysMsg(f"Found {num_runes} runes in runebook", 946)

    button_height = 30
    button_spacing = 5
    gump_width = 200
    gump_height = 60 + (num_runes * (button_height + button_spacing))

    g = API.CreateGump()
    g.SetRect(100, 100, gump_width, gump_height)

    title = API.CreateGumpLabel(f"Runebook - {num_runes} Runes", hue=53)
    title.SetPos(10, 10)
    g.Add(title)

    rune_buttons = []
    for i in range(num_runes):
        btn = API.CreateSimpleButton(f"Rune {i + 1}", gump_width - 20, button_height)
        btn.SetPos(10, 40 + (i * (button_height + button_spacing)))
        API.AddControlOnClick(btn, make_callback(i))
        g.Add(btn)
        rune_buttons.append(btn)

    API.AddGump(g)

    last_selected_idx = [None]

    while not API.StopRequested:
        API.ProcessCallbacks()
        if clicked_rune[0] is not None:
            rune_idx = clicked_rune[0]
            clicked_rune[0] = None

            if last_selected_idx[0] is not None:
                rune_buttons[last_selected_idx[0]].ClearBackgroundColor()

            rune_buttons[rune_idx].SetBackgroundColor(0, 150, 0, 200)
            last_selected_idx[0] = rune_idx

            API.SysMsg(f"Recalling to rune {rune_idx + 1}...", 946)

            if not open_runebook():
                API.SysMsg("Failed to reopen runebook gump", 33)
                continue

            API.ReplyGump(50 + rune_idx, 0x59)
            API.Pause(0.5)
        API.Pause(0.1)
