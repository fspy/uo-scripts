# pyright: reportCallIssue=false
import time

import API
from _lib.utils import p


def spell_toggle(spell):
    while not API.StopRequested:
        API.CastSpell(spell)
        API.WaitForTarget(timeout=2)
        API.Target(API.LastTargetSerial)
        API.Pause(1)
        API.CastSpell(spell)


def hiding():
    while API.GetSkill("Hiding").Base < API.GetSkill("Hiding").Cap:
        API.UseSkill("Hiding")
        API.Pause(1)


def chest_check():
    chest_graphics = {0x0E40, 0x0E41}
    chest_hues = {0, 1109}  # , 1150, 2219, 2207}
    container = API.RequestTarget(10)

    for cg in chest_graphics:
        chests = API.FindTypeAll(cg, container)
        chests = filter(lambda c: c.Hue in chest_hues, chests)
        for chest in chests:
            API.MoveItem(chest, API.Backpack, 1)
            # API.HeadMsg(f"{chest.Hue}", chest.Serial, chest.Hue)
            # API.HeadMsg(f"{hex(chest.Graphic)}", chest.Serial)
            API.Pause(0.65)

        API.Pause(0.65)


def auto_coown():
    while not API.StopRequested:
        if API.HasGump(0x29B6C49):
            p("set permission to co-owner!")
            API.ReplyGump(2)
        API.Pause(0.1)


def grab_horned_kit():
    API.ContextMenu(0xC1269, 3)
    API.WaitForGump(0x69DA8520)
    API.ReplyGump(222, 0x69DA8520)


def grab_copper_hammer():
    API.ContextMenu(0xC1068, 3)
    API.WaitForGump(0x69DA8520)
    API.ReplyGump(223, 0x69DA8520)


def grab_bronze_hammer():
    API.ContextMenu(0xC1068, 3)
    API.WaitForGump(0x69DA8520)
    API.ReplyGump(225, 0x69DA8520)


def shadowjump():
    direction = -1
    while True:
        if API.Player.Mana < 8:
            API.HeadMsg("Swapping!", API.Player)
            direction *= -1
            while API.Player.ManaDiff > 0:
                API.Pause(0.1)

        API.CastSpell("Shadowjump")
        API.WaitForTarget()
        API.TargetLandRel(direction, 0)


def steal():
    while API.GetSkill("Stealing").Value < API.GetSkill("Stealing").Cap:
        API.UseSkill("Stealing")
        if API.WaitForTarget(timeout=0.5):
            API.Target(API.FindItem(0x40021F9D))
            API.Pause(1)

        if API.InJournal("successfully steal the item", True):
            API.Organizer("stealing")

        API.Pause(9)


def poisoning():
    weapon = API.RequestTarget()
    while API.GetSkill("Poisoning").Value < API.GetSkill("Poisoning").Cap:
        if not API.FindType(0x0F0A, API.Backpack):
            break
        API.UseSkill("Poisoning")
        API.WaitForTarget()
        API.Target(API.Found)
        API.WaitForTarget()
        API.Target(weapon)
        API.Pause(10)


def mine_stuff():
    pickaxe = API.FindType(0x0E86, API.Backpack)

    def find_niter():
        for g in [0x1361, 0x1367, 0x1364, 0x1365]:
            if API.FindType(g, range=2):
                return API.Found
        return None

    niter = find_niter()
    while pickaxe and niter:
        API.UseObject(pickaxe)
        API.WaitForTarget()
        API.Target(niter)
        API.Pause(0.65)
        pickaxe = API.FindType(0x0E86, API.Backpack)
        niter = find_niter()


def show_runebook_runes(rb_serial):
    """
    Display a gump with buttons for each rune in a runebook.
    Clicking a button recalls to that rune.

    Args:
        rb_serial: The runebook item serial
    """

    def open_runebook(timeout=2.0):
        """Open runebook and wait for gump, returns True if successful."""
        if not API.HasGump(0x59):
            API.UseObject(rb_serial, True)
            start = time.time()
            while not API.HasGump(0x59) and time.time() - start < timeout:
                API.Pause(0.1)
        return API.HasGump(0x59)

    # Shared state for callback communication
    clicked_rune = [None]

    def make_callback(rune_index):
        def callback():
            clicked_rune[0] = rune_index

        return callback

    # Open the runebook gump initially
    if not open_runebook():
        p("Failed to open runebook gump")
        return

    # Count runes by counting "default" in gump contents
    gump_content = API.GetGumpContents(0x59)
    num_runes = gump_content.count("default")

    if num_runes == 0:
        p("No runes found in runebook")
        return

    p(f"Found {num_runes} runes in runebook")

    # Create a gump with buttons for each rune
    button_height = 30
    button_spacing = 5
    gump_width = 200
    gump_height = 60 + (num_runes * (button_height + button_spacing))

    g = API.CreateGump()
    g.SetRect(100, 100, gump_width, gump_height)

    # Add title label
    title = API.CreateGumpLabel(f"Runebook - {num_runes} Runes", hue=53)
    title.SetPos(10, 10)
    g.Add(title)

    # Create a button for each rune with click callbacks
    rune_buttons = []
    for i in range(num_runes):
        btn = API.CreateSimpleButton(f"Rune {i + 1}", gump_width - 20, button_height)
        btn.SetPos(10, 40 + (i * (button_height + button_spacing)))
        API.AddControlOnClick(btn, make_callback(i))
        g.Add(btn)
        rune_buttons.append(btn)

    API.AddGump(g)

    # Track last selected button for highlighting
    last_selected_idx = [None]

    # Wait for button clicks using callbacks
    while not API.StopRequested:
        API.ProcessCallbacks()
        if clicked_rune[0] is not None:
            rune_idx = clicked_rune[0]
            clicked_rune[0] = None  # Reset

            # Clear previous highlight
            if last_selected_idx[0] is not None:
                rune_buttons[last_selected_idx[0]].ClearBackgroundColor()

            # Highlight this button (green background)
            rune_buttons[rune_idx].SetBackgroundColor(0, 150, 0, 200)
            last_selected_idx[0] = rune_idx

            p(f"Recalling to rune {rune_idx + 1}...")

            # Make sure runebook gump is open before recalling
            if not open_runebook():
                p("Failed to reopen runebook gump")
                continue

            # Recall button formula: 50 + rune_index
            API.ReplyGump(50 + rune_idx, 0x59)
            API.Pause(0.5)
        API.Pause(0.1)


def last_object_target():
    last = API.LastTargetSerial
    tar = API.RequestTarget()
    while tar:
        API.UseObject(tar)
        API.WaitForTarget()
        API.Target(last)
        API.Pause(0.05)


rb = 0x403C2DB3
show_runebook_runes(rb)
# spell_toggle("Combat Training")
