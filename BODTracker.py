"""
BOD Timer Tracker

Tracks Bulk Order Deed (BOD) timers across all characters on a server.
Automatically accepts BODs and records cooldown timers.

Usage:
1. Run this script (it stays running in background)
2. Walk up to a profession NPC (blacksmith, tailor, cook, etc.)
3. Right-click NPC → "Bulk Order Info"
4. Script auto-accepts all available BODs and records the timer
5. Get notified when BODs become ready

Features:
- Tracks timers for all characters on the server
- Shows BOD status for all characters on login
- Notifies when BODs become ready
- Supports 8 professions: Alchemy, Blacksmithing, Carpentry, Cooking,
  Fletching, Inscription, Tailoring, Tinkering
"""

import API
import time
import re
import json
from lib.journal import find_entry
from lib.utils import format_time_remaining

# ============================================================================
# CONFIGURATION
# ============================================================================

NPC_SUFFIXES = {
    "alchemist": "Alchemy",
    "blacksmith": "Blacksmithing",
    "weaponsmith": "Blacksmithing",
    "armourer": "Blacksmithing",
    "carpenter": "Carpentry",
    "cook": "Cooking",
    "bowyer": "Fletching",
    "scribe": "Inscription",
    "tailor": "Tailoring",
    "tinker": "Tinkering",
}

BOD_GUMP_ID = 0x9BADE6EA  # Small BOD gump
LARGE_BOD_GUMP_ID = 0xBE0DAD1E  # Large BOD gump
CONTEXT_MENU_BOD_INFO = 1  # "Bulk Order Info" context menu entry
ACCEPT_BUTTON = 1  # OK button on BOD gump
RETRIGGER_DELAY = 2.0  # Wait 2s between accept and re-trigger (for saves)
READY_CHECK_INTERVAL = 60  # Check for ready BODs every 60s
READY_REMINDER_INTERVAL = 300  # Re-notify every 5 min
STORAGE_KEY = "BODTimers"

# Colors
HUE_SUCCESS = 62  # Green - BOD accepted, timer saved
HUE_READY = 37  # Gold/Yellow - BOD is ready!
HUE_INFO = 946  # Gray - status info
HUE_ALERT = 32  # Red - errors/warnings

# Timer message regex
TIMER_MSG_PATTERN = r"An offer may be available in about (\d+) minute"


# ============================================================================
# TIMER STORAGE (Server scope - cross-character)
# ============================================================================


def load_all_timers():
    """
    Load timers for all characters on this server.

    Returns:
        dict: {char_name: {profession: timestamp}}
    """
    raw = API.GetPersistentVar(STORAGE_KEY, "", API.PersistentVar.Server)

    if not raw:
        return {}

    try:
        timers = json.loads(raw)
        # Ensure all values are floats (defensive coding)
        for char_name in timers:
            for prof in timers[char_name]:
                timers[char_name][prof] = float(timers[char_name][prof])
        return timers
    except (ValueError, TypeError, KeyError):
        # If JSON parsing fails, return empty dict (fresh start)
        return {}


def save_all_timers(timers):
    """
    Save all timers to Server-scoped persistent storage.

    Args:
        timers (dict): {char_name: {profession: timestamp}}
    """
    # Remove characters with no timers before saving
    cleaned = {char: profs for char, profs in timers.items() if profs}
    raw = json.dumps(cleaned)
    API.SavePersistentVar(STORAGE_KEY, raw, API.PersistentVar.Server)


def save_timer(char_name, profession, ready_at):
    """
    Update a single timer and save to storage.

    Args:
        char_name (str): Character name
        profession (str): Profession name (e.g., "Alchemy")
        ready_at (float): Unix timestamp when BOD becomes ready
    """
    timers = load_all_timers()

    if char_name not in timers:
        timers[char_name] = {}

    timers[char_name][profession] = ready_at
    save_all_timers(timers)


# ============================================================================
# NPC DETECTION & PROFESSION PARSING
# ============================================================================


def detect_profession_from_props(props):
    """
    Extract profession from NPC NameAndProps tooltip.

    Args:
        props (str): NPC properties like "Afrika The Alchemist"

    Returns:
        str: Profession name or None
    """
    if not props:
        return None

    props_lower = props.lower()
    for suffix, profession in NPC_SUFFIXES.items():
        if suffix in props_lower:
            return profession

    return None


def find_profession_npc(preferred_name=None):
    """
    Find nearby profession NPC using NameAndProps().

    Args:
        preferred_name (str): If provided, prefer NPC with this name (from journal speaker)

    Returns:
        tuple: (serial, profession) or (None, None)
    """
    candidates = []  # List of (serial, profession, distance, name_match)
    player_pos = (API.Player.X, API.Player.Y)

    for mob in API.GetAllMobiles(distance=5):
        if not mob.Name:
            continue

        try:
            props = mob.NameAndProps(wait=False, timeout=2)
            profession = detect_profession_from_props(props)
            if profession:
                # Calculate distance to player
                dist = abs(mob.X - player_pos[0]) + abs(mob.Y - player_pos[1])
                # Check if name matches preferred (journal speaker)
                name_match = preferred_name and mob.Name == preferred_name
                candidates.append((mob.Serial, profession, dist, name_match))
        except:
            continue

    if not candidates:
        return None, None

    # Sort: prioritize name match first, then closest distance
    candidates.sort(key=lambda x: (not x[3], x[2]))

    return candidates[0][0], candidates[0][1]


# ============================================================================
# BOD GUMP HANDLING
# ============================================================================


def detect_bod_gump():
    """
    Check if BOD gump is open (small or large).

    Returns:
        int: Gump ID if BOD gump is open, None otherwise
    """
    # Check for both small and large BOD gumps
    for gump_id in (BOD_GUMP_ID, LARGE_BOD_GUMP_ID):
        if API.HasGump(gump_id):
            return gump_id
    return None


def accept_bod(gump_id):
    """
    Accept BOD by clicking the OK button.

    Args:
        gump_id (int): BOD gump ID
    """
    API.ReplyGump(ACCEPT_BUTTON, gump_id)


def trigger_bod_check(npc_serial):
    """
    Send context menu to NPC to request BOD info.

    Args:
        npc_serial (int): NPC serial number
    """
    API.ContextMenu(npc_serial, CONTEXT_MENU_BOD_INFO)


# ============================================================================
# JOURNAL PARSING
# ============================================================================


def check_for_timer_message():
    """
    Check journal for timer message and extract minutes and speaker name.

    Returns:
        tuple: (minutes, speaker_name) or (None, None) if not found
    """
    entry = find_entry("offer may be available", timeout=0.1, seconds_back=3)
    if not entry:
        return None, None

    match = re.search(TIMER_MSG_PATTERN, entry.Text)
    if match:
        minutes = int(match.group(1))
        speaker_name = entry.Name if entry.Name else None
        return minutes, speaker_name

    return None, None


# ============================================================================
# NOTIFICATIONS
# ============================================================================


def show_startup_status():
    """Display all BOD timers on script start."""
    API.SysMsg("=" * 50, HUE_SUCCESS)
    API.SysMsg("=== BOD Timer Tracker ===", HUE_SUCCESS)
    API.SysMsg("=" * 50, HUE_SUCCESS)

    timers = load_all_timers()
    now = time.time()

    if not timers:
        API.SysMsg("No timers recorded yet.", HUE_INFO)
        API.SysMsg("Walk up to a profession NPC and use Bulk Order Info", HUE_INFO)
        return

    ready_count = 0
    for char_name, profs in timers.items():
        for profession, ready_at in profs.items():
            remaining = ready_at - now
            status = format_time_remaining(remaining)

            if remaining <= 0:
                hue = HUE_READY
                ready_count += 1
            else:
                hue = HUE_INFO

            API.SysMsg(f"{char_name} - {profession}: {status}", hue)

    if ready_count > 0:
        API.SysMsg(f"{ready_count} BOD(s) ready to collect!", HUE_READY)
        API.HeadMsg(f"{ready_count} BOD(s) READY!", API.Player.Serial, HUE_READY)

    API.SysMsg("=" * 50, HUE_SUCCESS)


def notify_bod_accepted(profession):
    """
    Notify player that a BOD was accepted.

    Args:
        profession (str): Profession name
    """
    API.SysMsg(f"Accepted {profession} BOD!", HUE_SUCCESS)


def notify_timer_saved(profession, minutes):
    """
    Notify player that timer was recorded.

    Args:
        profession (str): Profession name
        minutes (int): Minutes until next BOD
    """
    formatted = format_time_remaining(minutes * 60)
    API.SysMsg(f"{profession} BOD in {formatted}", HUE_SUCCESS)


def notify_bod_ready(char_name, profession):
    """
    Notify player that a BOD is ready.

    Args:
        char_name (str): Character name
        profession (str): Profession name
    """
    msg = f"{char_name} - {profession} BOD READY!"
    API.SysMsg(msg, HUE_READY)
    API.HeadMsg("BOD READY!", API.Player.Serial, HUE_READY)


# ============================================================================
# BOD STATUS GUMP UI
# ============================================================================


class BODStatusGump:
    """Interactive gump showing BOD timers for all characters."""

    def __init__(self):
        """Initialize the gump in expanded state."""
        self.gump = None
        self.expanded = True
        self.last_update = 0
        self.width = 350
        self.collapsed_height = 40
        self.header_height = 30

    def create(self):
        """Create and display the gump."""
        if self.gump:
            API.CloseGumps()  # Close all script-created gumps
        
        self.gump = API.CreateGump(acceptMouseInput=True, canMove=True)
        self.gump.SetX(100)
        self.gump.SetY(100)

        if self.expanded:
            self._create_expanded()
        else:
            self._create_collapsed()

        API.AddGump(self.gump)

    def _create_collapsed(self):
        """Create collapsed bar view showing earliest BOD."""
        self.gump.SetWidth(self.width)
        self.gump.SetHeight(self.collapsed_height)

        # Background
        bg = API.CreateGumpColorBox(0.8, "#1a1a1a")
        bg.SetWidth(self.width)
        bg.SetHeight(self.collapsed_height)
        bg.SetX(0)
        bg.SetY(0)
        self.gump.Add(bg)

        # Get status text
        status_text = self._get_collapsed_status()

        # Status label
        label = API.CreateGumpTTFLabel(status_text, 16, "#FFFFFF", "alagard")
        label.SetX(10)
        label.SetY(12)
        self.gump.Add(label)

        # Expand button (▼)
        expand_btn = API.CreateGumpButton("▼", 996)
        expand_btn.SetX(self.width - 30)
        expand_btn.SetY(8)
        self.gump.Add(expand_btn)

    def _create_expanded(self):
        """Create expanded view showing all characters and BODs."""
        timers = load_all_timers()
        now = time.time()

        # Calculate height based on content
        char_count = len(timers)
        bod_count = sum(len(profs) for profs in timers.values())
        content_height = self.header_height + (char_count * 25) + (bod_count * 22) + 20
        total_height = min(content_height, 500)  # Cap at 500px

        self.gump.SetWidth(self.width)
        self.gump.SetHeight(total_height)

        # Background
        bg = API.CreateGumpColorBox(0.9, "#1a1a1a")
        bg.SetWidth(self.width)
        bg.SetHeight(total_height)
        bg.SetX(0)
        bg.SetY(0)
        self.gump.Add(bg)

        # Header
        header_bg = API.CreateGumpColorBox(1.0, "#2d2d2d")
        header_bg.SetWidth(self.width)
        header_bg.SetHeight(self.header_height)
        header_bg.SetX(0)
        header_bg.SetY(0)
        self.gump.Add(header_bg)

        title = API.CreateGumpTTFLabel("BOD Tracker", 18, "#FFFFFF", "alagard")
        title.SetX(10)
        title.SetY(6)
        self.gump.Add(title)

        # Collapse button (▲)
        collapse_btn = API.CreateGumpButton("▲", 996)
        collapse_btn.SetX(self.width - 30)
        collapse_btn.SetY(3)
        self.gump.Add(collapse_btn)

        # Content area with scrolling if needed
        if content_height > 500:
            scroll = API.CreateGumpScrollArea(
                0, self.header_height, self.width, total_height - self.header_height
            )
            self.gump.Add(scroll)
            container = scroll
            y_offset = 10
        else:
            container = self.gump
            y_offset = self.header_height + 10

        # Render character entries
        if not timers:
            no_data = API.CreateGumpTTFLabel(
                "No BODs tracked yet", 16, "#808080", "alagard"
            )
            no_data.SetX(10)
            no_data.SetY(y_offset)
            container.Add(no_data)
        else:
            y_offset = self._render_character_entries(container, timers, now, y_offset)

    def _render_character_entries(self, container, timers, now, y_offset):
        """Render character sections with their BODs."""
        # Sort: current char first, then alphabetically
        current_char = API.Player.Name
        sorted_chars = sorted(timers.keys(), key=lambda c: (c != current_char, c))

        for char_name in sorted_chars:
            profs = timers[char_name]
            if not profs:
                continue

            # Character header (divider line)
            divider_color = "#4a9eff" if char_name == current_char else "#606060"
            char_label = API.CreateGumpTTFLabel(
                f"{char_name} " + "─" * 30, 14, divider_color, "alagard"
            )
            char_label.SetX(10)
            char_label.SetY(y_offset)
            container.Add(char_label)
            y_offset += 25

            # Sort BODs: ready first, then by time (soonest first)
            sorted_profs = sorted(profs.items(), key=lambda x: (x[1] > now, x[1]))

            for profession, ready_at in sorted_profs:
                remaining = ready_at - now
                status = format_time_remaining(remaining)

                # Color code: green/gold for ready, white for waiting
                if remaining <= 0:
                    color = "#00ff00"  # Bright green for ready
                    text = f"  {profession:<20} {status}"
                else:
                    color = "#cccccc"  # Light gray for waiting
                    text = f"  {profession:<20} {status}"

                bod_label = API.CreateGumpTTFLabel(text, 14, color, "alagard")
                bod_label.SetX(10)
                bod_label.SetY(y_offset)
                container.Add(bod_label)
                y_offset += 22

            y_offset += 5  # Extra space between characters

        return y_offset

    def _get_collapsed_status(self):
        """Get status text for collapsed bar."""
        timers = load_all_timers()
        current_char = API.Player.Name
        now = time.time()

        if not timers or current_char not in timers:
            return "No BODs tracked"

        char_timers = timers[current_char]
        if not char_timers:
            return "No BODs tracked"

        # Check for ready BODs
        ready_bods = [(prof, ts) for prof, ts in char_timers.items() if ts <= now]

        if ready_bods:
            count = len(ready_bods)
            return f"{current_char}: {count} READY!"

        # Show earliest timer
        earliest_prof, earliest_time = min(char_timers.items(), key=lambda x: x[1])
        remaining = earliest_time - now
        status = format_time_remaining(remaining)
        return f"{current_char} - {earliest_prof}: {status}"

    def update(self):
        """Refresh the gump content if enough time has passed."""
        now = time.time()
        if now - self.last_update < 60:  # Update once per minute
            return

        self.last_update = now
        self.create()  # Recreate gump with updated content

    def toggle(self):
        """Toggle between expanded and collapsed states."""
        self.expanded = not self.expanded
        self.create()

    def close(self):
        """Close the gump."""
        if self.gump:
            API.CloseGumps()  # Close all script-created gumps
            self.gump = None


# ============================================================================
# MAIN LOOP
# ============================================================================


def main():
    """Main script loop."""
    # Create and show status gump
    status_gump = BODStatusGump()
    status_gump.create()

    # State tracking
    current_npc_serial = None
    current_profession = None
    last_ready_check = 0
    last_notifications = {}  # {(char, prof): timestamp}

    API.SysMsg("BOD Tracker running... (press stop to exit)", HUE_INFO)

    while not API.StopRequested:
        now = time.time()

        # Update gump periodically
        status_gump.update()

        # A) Check for BOD gump
        gump_id = detect_bod_gump()
        if gump_id:
            # Find profession NPC if we don't have one
            if not current_profession:
                current_npc_serial, current_profession = find_profession_npc()
                if current_profession:
                    API.SysMsg(f"Detected {current_profession} NPC", HUE_INFO)
                else:
                    API.SysMsg("Could not detect profession NPC!", HUE_ALERT)

            # Accept the BOD
            accept_bod(gump_id)
            notify_bod_accepted(current_profession or "Unknown")

            # Wait and re-trigger
            API.Pause(RETRIGGER_DELAY)
            if current_npc_serial:
                trigger_bod_check(current_npc_serial)
            continue

        # B) Check for timer message
        minutes, speaker_name = check_for_timer_message()
        if minutes is not None:
            profession = current_profession
            if not profession:
                # Fallback: try to detect using speaker name (most reliable)
                _, profession = find_profession_npc(preferred_name=speaker_name)

            if profession:
                ready_at = now + (minutes * 60)
                save_timer(API.Player.Name, profession, ready_at)
                notify_timer_saved(profession, minutes)
                # Refresh gump immediately to show new timer
                status_gump.create()
                # Clear timer message from journal
                API.ClearJournal("offer may be available")
            else:
                API.SysMsg(
                    "Timer detected but couldn't identify profession!", HUE_ALERT
                )

            # Reset state
            current_npc_serial = None
            current_profession = None

        # C) Periodic ready check
        if now - last_ready_check > READY_CHECK_INTERVAL:
            last_ready_check = now
            timers = load_all_timers()

            for char_name, profs in timers.items():
                for profession, ready_at in profs.items():
                    if ready_at <= now:
                        key = (char_name, profession)
                        last_notif = last_notifications.get(key, 0)
                        if now - last_notif > READY_REMINDER_INTERVAL:
                            notify_bod_ready(char_name, profession)
                            last_notifications[key] = now

        API.Pause(0.5)

    # Clean up on exit
    status_gump.close()


# ============================================================================
# ENTRY POINT
# ============================================================================

main()
