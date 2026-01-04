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

# ============================================================================
# CONFIGURATION
# ============================================================================

NPC_SUFFIXES = {
    "alchemist": "Alchemy",
    "blacksmith": "Blacksmithing",
    "carpenter": "Carpentry",
    "cook": "Cooking",
    "bowyer": "Fletching",
    "scribe": "Inscription",
    "tailor": "Tailoring",
    "tinker": "Tinkering",
}

BOD_GUMP_ID = 0x9BADE6EA
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
    timers = {}

    if not raw:
        return timers

    # Format: "CharName:prof=timestamp,prof=timestamp;CharName2:prof=timestamp"
    for char_block in raw.split(";"):
        if ":" not in char_block:
            continue

        char_name, profs = char_block.split(":", 1)
        timers[char_name] = {}

        for entry in profs.split(","):
            if "=" in entry:
                prof, ts = entry.split("=", 1)
                try:
                    timers[char_name][prof] = float(ts)
                except ValueError:
                    pass  # Skip invalid entries

    return timers


def save_all_timers(timers):
    """
    Save all timers to Server-scoped persistent storage.

    Args:
        timers (dict): {char_name: {profession: timestamp}}
    """
    parts = []
    for char_name, profs in timers.items():
        if not profs:
            continue  # Skip chars with no timers
        prof_parts = [f"{p}={t}" for p, t in profs.items()]
        parts.append(f"{char_name}:{','.join(prof_parts)}")

    raw = ";".join(parts)
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
# TIME FORMATTING
# ============================================================================


def format_time_remaining(seconds):
    """
    Format seconds as human-readable time.

    Args:
        seconds (float): Seconds remaining

    Returns:
        str: Formatted time like "5h 59m", "45m", or "READY!"
    """
    if seconds <= 0:
        return "READY!"

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)

    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


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
                name_match = (preferred_name and mob.Name == preferred_name)
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
    Check if BOD gump is open.

    Returns:
        int: Gump ID if BOD gump is open, None otherwise
    """
    gump_id = API.HasGump(BOD_GUMP_ID)
    if gump_id:
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
    entries = API.GetJournalEntries(3, "offer may be available")
    if not entries:
        return None, None

    for entry in entries:
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
# MAIN LOOP
# ============================================================================


def main():
    """Main script loop."""
    # Show startup status
    show_startup_status()

    # State tracking
    current_npc_serial = None
    current_profession = None
    last_ready_check = 0
    last_notifications = {}  # {(char, prof): timestamp}

    API.SysMsg("BOD Tracker running... (press stop to exit)", HUE_INFO)

    while not API.StopRequested:
        now = time.time()

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


# ============================================================================
# ENTRY POINT
# ============================================================================

main()
