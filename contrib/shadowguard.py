######################
# Shadowguard Ultimate Script
# death adders with help from Dorana script
# Final Version:#  debugged beta
######################

import json
import os

import API

# --- CONFIGURATION FILE PATH ---
SHADOWGUARD_CONFIG_FILE = os.path.join(os.getcwd(), "shadowguard_gump_positions.json")

# --- MODERN UI COLORS ---
MODERN_COLORS = {
    "background": "#1a1a1a",
    "header": "#4a90e2",
    "accent": "#6c5ce7",
    "success": "#00b894",
    "warning": "#fdcb6e",
    "danger": "#e17055",
    "text_primary": "#ffffff",
    "text_secondary": "#b2bec3",
    "card_bg": "#2d3436",
    "progress_bg": "#333333",
    "border": "#636e72",
    "dead_boss": "#636e72",  # Gray for dead bosses
}

# Modern Icons and Symbols
MODERN_ICONS = {
    "location": "📍",
    "complete": "✓",
    "progress": "⚡",
    "bottles": "🍾",
    "enemies": "⚔️",
    "pairs": "🌳",
    "apple": "🍎",
    "phylactery": "💀",
    "armor": "🛡️",
    "flames": "🔥",
    "fountain": "💧",
    "pieces": "🧩",
    "lobby": "🏛️",
    "bar": "🍺",
    "orchard": "🌳",
    "armory": "⚔️",
    "belfry": "🔔",
    "roof": "🏠",
}

# --- ROOM DETECTION GRAPHICS ---
# Using graphic IDs that will be placed in the gumps as icons
ROOM_GRAPHICS = {
    "Lobby": [],
    "Bar": [0x099B],  # Bottles
    "Orchard": [0x0D01],  # Trees
    "Armory": [0x19AB, 0x42B4, 0x1512],  # Flames, Phylacteries, Armor
    "Belfry": [0x0F4B],  # Bell graphic
    "Fountain": [0x9BE5, 0x9BFF],  # Spigots and drains
    "Roof": [33813],  # Using a boss ID as a placeholder graphic
}

# --- BOSS IDS FOR ROOF ---
ROOF_BOSS_IDS = [33813, 2951, 1071, 33779]
ROOF_BOSS_NAMES = {33813: "Ju'nar", 2951: "Vial", 1071: "Anon", 33779: "Virtuebane"}
# --- GRAPHICS & CONFIG (From user's script) ---
SPIGOT_GRAPHICS = [0x9BE5, 0x9C02, 0x9BF2]
DRAIN_GRAPHIC = 0x9BFF
FLAMES_GRAPHIC = 0x19AB
CURSED_ARMOR_GRAPHIC = 0x1512
CURSED_ARMOR_GRAPHIC_2 = 0x151A
PHILACTERY_GRAPHIC = 0x42B4
CORRUPT_PHYLACTERY_HUE = 2752
PURIFIED_PHYLACTERY_HUE = 1166
CANAL_PIECES = {
    0x9BEF: "T-Piece",
    0x9BF4: "Diagonal",
    0x9BEB: "Corner",
    0x9BF8: "Cross",
    0x9BE7: "Straight",
    0x9BFC: "Angled",
}

# Enhanced GUMP_CONFIG with proper dimensions
GUMP_CONFIG = {
    "Overview": {"x": 50, "y": 50, "w": 340, "h": 420},  # Increased height
    "Bar": {"x": 100, "y": 100, "w": 380, "h": 180},
    "Orchard": {"x": 150, "y": 100, "w": 420, "h": 180},
    "Armory": {"x": 200, "y": 100, "w": 460, "h": 260},
    "Fountain": {"x": 250, "y": 100, "w": 420, "h": 220},
    "Belfry": {"x": 300, "y": 100, "w": 320, "h": 120},
    "Roof": {"x": 350, "y": 100, "w": 380, "h": 200},  # Increased for boss tracking
}

# --- SCRIPT STATE ---
rooms_complete = {
    "Bar": False,
    "Orchard": False,
    "Armory": False,
    "Fountain": False,
    "Belfry": False,
    "Roof": False,
}
roof_bosses_dead = {33813: False, 2951: False, 1071: False, 33779: False}
roof_current_boss_index = 0  # Track which boss we're waiting for
tree_partners = {}
puzzle_path_locations = {}
current_stats = {
    "current_room": "Lobby",
    "bar_bottles_used": 0,
    "orchard_pairs_complete": 0,
    "armory_phylacteries_purified": 0,
    "armory_armor_destroyed": 0,
    "fountain_pieces_placed": 0,
}
active_gump_name = "None"
_current_gump_instance = None
_open_gump_instances = {}
gump_controls = {
    "Overview": {},
    "Bar": {},
    "Orchard": {},
    "Armory": {},
    "Fountain": {},
    "Belfry": {},
    "Roof": {},
}
last_player_hp = 100  # Track player HP for death detection


# --- HELPER FUNCTIONS ---
class TriPoint:
    def __init__(self, x, y, z):
        self.X = x
        self.Y = y
        self.Z = z

    def __eq__(self, other):
        return self.X == other.X and self.Y == other.Y and self.Z == other.Z

    def __hash__(self):
        return hash((self.X, self.Y, self.Z))


def safe_get_coords(obj):
    try:
        x = obj.X if hasattr(obj, "X") else obj.Position.X
        y = obj.Y if hasattr(obj, "Y") else obj.Position.Y
        z = obj.Z if hasattr(obj, "Z") else obj.Position.Z
        return int(x), int(y), int(z)
    except:
        return 0, 0, 0


# --- JSON CONFIGURATION FUNCTIONS ---
def load_gump_positions():
    global GUMP_CONFIG
    default_gump_config = {name: data.copy() for name, data in GUMP_CONFIG.items()}
    API.SysMsg(
        f"Loading Modern UI positions from: {os.path.abspath(SHADOWGUARD_CONFIG_FILE)}",
        67,
    )

    if os.path.exists(SHADOWGUARD_CONFIG_FILE):
        try:
            if os.path.getsize(SHADOWGUARD_CONFIG_FILE) > 0:
                with open(SHADOWGUARD_CONFIG_FILE, "r") as f:
                    loaded_positions = json.load(f)
                    for gump_name, pos_data in loaded_positions.items():
                        if gump_name in default_gump_config:
                            default_gump_config[gump_name]["x"] = pos_data.get(
                                "x", default_gump_config[gump_name]["x"]
                            )
                            default_gump_config[gump_name]["y"] = pos_data.get(
                                "y", default_gump_config[gump_name]["y"]
                            )
                GUMP_CONFIG = default_gump_config
                API.SysMsg("Modern UI positions loaded successfully.", 67)
            else:
                API.SysMsg("Config file empty. Creating with modern defaults.", 33)
                save_gump_positions()
        except Exception as e:
            API.SysMsg(f"Error loading config: {e}. Using defaults.", 33)
            save_gump_positions()
    else:
        API.SysMsg("Config not found. Creating with modern defaults.", 67)
        save_gump_positions()


def save_gump_positions():
    save_data = {}
    for gump_name, config_data in GUMP_CONFIG.items():
        save_data[gump_name] = {"x": config_data["x"], "y": config_data["y"]}
    try:
        with open(SHADOWGUARD_CONFIG_FILE, "w") as f:
            json.dump(save_data, f, indent=4)
        API.SysMsg("Modern UI positions saved.", 68)
    except Exception as e:
        API.SysMsg(f"Failed to save positions: {e}", 33)


# --- ENHANCED ROOM DETECTION ---
def get_current_room():
    """Enhanced room detection using proper graphic IDs, including the roof."""
    search_range = 20

    # --- ADDED: Check for specific roof graphic first for reliability ---
    if API.FindTypeAll(19343, range=search_range):
        return "Roof"

    # Check for Fountain (most specific)
    if any(API.FindTypeAll(graphic, range=search_range) for graphic in SPIGOT_GRAPHICS):
        return "Fountain"

    # Check for Armory
    if (
        API.FindTypeAll(FLAMES_GRAPHIC, range=search_range)
        or API.FindTypeAll(CURSED_ARMOR_GRAPHIC, range=search_range)
        or API.FindTypeAll(CURSED_ARMOR_GRAPHIC_2, range=search_range)
        or API.FindTypeAll(PHILACTERY_GRAPHIC, range=search_range)
    ):
        return "Armory"

    # Check for Orchard
    trees = API.FindTypeAll(0x0D01, range=search_range)
    if trees:
        for tree in trees:
            if "cypress" in API.ItemNameAndProps(tree.Serial, True).lower():
                return "Orchard"

    # Check for Bar
    if API.FindTypeAll(0x099B, range=search_range) and API.NearestMobiles(
        [API.Notoriety.Enemy, API.Notoriety.Murderer], 15
    ):
        return "Bar"

    # Check for Roof (fallback by boss IDs)
    for boss_id in ROOF_BOSS_IDS:
        if API.FindTypeAll(boss_id, range=search_range):
            return "Roof"

    # Check for Belfry
    if any(API.FindTypeAll(graphic, range=search_range) for graphic in [0x6F5, 0x6F6]):
        return "Belfry"

    return "Lobby"


# --- MODERN UI HELPER FUNCTIONS ---
def create_modern_card(gump, x, y, width, height, opacity=0.9):
    card = API.CreateGumpColorBox(opacity=opacity, color=MODERN_COLORS["card_bg"])
    card.SetX(x)
    card.SetY(y)
    card.SetWidth(width)
    card.SetHeight(height)
    gump.Add(card)


def create_stat_row_with_icon(
    gump, x, y, graphic_id, icon, label, value, value_color="text_primary"
):
    """Create a stat row with both graphic and text icon"""
    # Add the graphic icon if provided
    if graphic_id:
        try:
            art = API.CreateGumpItemPic(graphic_id, 20, 20)
            art.SetX(x)
            art.SetY(y - 2)
            gump.Add(art)
            x_offset = 25  # Move text to the right of the graphic
        except:
            x_offset = 0
    else:
        x_offset = 0

    # Add text icon
    icon_label = API.CreateGumpLabel(icon, 1153)
    icon_label.SetX(x + x_offset)
    icon_label.SetY(y)
    gump.Add(icon_label)

    # Add label
    label_obj = API.CreateGumpLabel(label, 1153)
    label_obj.SetX(x + x_offset + 25)
    label_obj.SetY(y)
    gump.Add(label_obj)

    # Add value
    value_obj = API.CreateGumpLabel(str(value), 1153)
    value_obj.SetX(x + x_offset + 200)
    value_obj.SetY(y)
    gump.Add(value_obj)

    return value_obj


def create_stat_row(gump, x, y, icon, label, value, value_color="text_primary"):
    icon_label = API.CreateGumpLabel(icon, 1153)
    icon_label.SetX(x)
    icon_label.SetY(y)
    gump.Add(icon_label)
    label_obj = API.CreateGumpLabel(label, 1153)
    label_obj.SetX(x + 25)
    label_obj.SetY(y)
    gump.Add(label_obj)
    value_obj = API.CreateGumpLabel(str(value), 1153)
    value_obj.SetX(x + 200)
    value_obj.SetY(y)
    gump.Add(value_obj)
    return value_obj


def add_room_graphics(gump, room_name):
    """Helper function to add item pics to gumps in header area"""
    config = GUMP_CONFIG[room_name]
    art_x, art_y = config["w"] - 120, 5  # Position in header area
    for graphic_id in ROOM_GRAPHICS.get(room_name, []):
        try:
            art = API.CreateGumpItemPic(graphic_id, 25, 25)
            art.SetX(art_x)
            art.SetY(art_y)
            gump.Add(art)
            art_x += 30  # Move right for the next icon
        except Exception as e:
            API.SysMsg(
                f"Failed to create gump art {graphic_id} for {room_name}: {e}", 33
            )


# --- MODERN GUMP FRAMEWORK ---
def close_all_gumps():
    global active_gump_name, _current_gump_instance, _open_gump_instances
    gumps_to_remove = []
    for gump_name, gump_obj in list(_open_gump_instances.items()):
        try:
            GUMP_CONFIG[gump_name]["x"] = int(gump_obj.GetX())
            GUMP_CONFIG[gump_name]["y"] = int(gump_obj.GetY())
        except:
            pass
        finally:
            gumps_to_remove.append(gump_name)
    for name_to_remove in gumps_to_remove:
        if name_to_remove in _open_gump_instances:
            del _open_gump_instances[name_to_remove]
    if gumps_to_remove:
        save_gump_positions()
    _current_gump_instance = None
    active_gump_name = "None"
    try:
        API.CloseGumps()
        API.Pause(0.2)
    except:
        pass


def create_modern_base_gump(name):
    global active_gump_name, _current_gump_instance, _open_gump_instances
    if _current_gump_instance is not None:
        close_all_gumps()
    config_for_gump = GUMP_CONFIG[name]
    gump = API.CreateGump(True, True)
    gump.SetX(config_for_gump["x"])
    gump.SetY(config_for_gump["y"])
    gump.SetWidth(config_for_gump["w"])
    gump.SetHeight(config_for_gump["h"])

    def on_gump_manual_close():
        global active_gump_name, _current_gump_instance, _open_gump_instances
        if name in _open_gump_instances and _open_gump_instances[name] is gump:
            try:
                GUMP_CONFIG[name]["x"] = int(gump.GetX())
                GUMP_CONFIG[name]["y"] = int(gump.GetY())
                save_gump_positions()
            except:
                pass
            finally:
                if name in _open_gump_instances:
                    del _open_gump_instances[name]
                if _current_gump_instance is gump:
                    _current_gump_instance = None
                    active_gump_name = "None"
                API.Pause(0.2)

    API.AddControlOnDisposed(gump, on_gump_manual_close)
    main_bg = API.CreateGumpColorBox(opacity=0.95, color=MODERN_COLORS["background"])
    main_bg.SetWidth(config_for_gump["w"])
    main_bg.SetHeight(config_for_gump["h"])
    gump.Add(main_bg)
    border = API.CreateGumpColorBox(opacity=0.3, color=MODERN_COLORS["border"])
    border.SetWidth(config_for_gump["w"])
    border.SetHeight(2)
    gump.Add(border)
    _current_gump_instance = gump
    active_gump_name = name
    _open_gump_instances[name] = gump
    return gump


def create_modern_overview_gump():
    gump = create_modern_base_gump("Overview")
    controls = gump_controls["Overview"]
    header_height = 35
    header_bg = API.CreateGumpColorBox(opacity=0.9, color=MODERN_COLORS["header"])
    header_bg.SetWidth(GUMP_CONFIG["Overview"]["w"])
    header_bg.SetHeight(header_height)
    gump.Add(header_bg)
    title = API.CreateGumpLabel("⚡ SHADOWGUARD TRACKER", 1153)
    title.SetX(15)
    title.SetY(8)
    gump.Add(title)
    create_modern_card(
        gump, 10, header_height + 10, GUMP_CONFIG["Overview"]["w"] - 20, 30
    )
    controls["location"] = API.CreateGumpLabel(
        f"{MODERN_ICONS['location']} Location: Unknown", 1153
    )
    controls["location"].SetX(20)
    controls["location"].SetY(header_height + 20)
    gump.Add(controls["location"])
    y_pos, card_height = header_height + 55, 32
    room_order = ["Bar", "Orchard", "Armory", "Fountain", "Belfry", "Roof"]
    for i, room in enumerate(room_order):
        create_modern_card(
            gump, 10, y_pos, GUMP_CONFIG["Overview"]["w"] - 20, card_height
        )
        room_icon = MODERN_ICONS.get(room.lower(), MODERN_ICONS["progress"])
        room_label = API.CreateGumpLabel(f"{room_icon} {room}:", 1153)
        room_label.SetX(20)
        room_label.SetY(y_pos + 8)
        gump.Add(room_label)
        controls[f"status_{room.lower()}"] = API.CreateGumpLabel("...", 1153)
        controls[f"status_{room.lower()}"].SetX(200)
        controls[f"status_{room.lower()}"].SetY(y_pos + 8)
        gump.Add(controls[f"status_{room.lower()}"])
        y_pos += card_height + 4
    create_modern_card(
        gump, 10, y_pos + 5, GUMP_CONFIG["Overview"]["w"] - 20, 40, opacity=0.95
    )
    controls["overall_progress"] = API.CreateGumpLabel(
        "🎯 Overall Progress: 0/6 (0%)", 1153
    )
    controls["overall_progress"].SetX(20)
    controls["overall_progress"].SetY(y_pos + 18)
    gump.Add(controls["overall_progress"])
    API.AddGump(gump)


def create_modern_roof_gump():
    gump = create_modern_base_gump("Roof")
    header_height = 35
    header_bg = API.CreateGumpColorBox(opacity=0.9, color=MODERN_COLORS["warning"])
    header_bg.SetWidth(GUMP_CONFIG["Roof"]["w"])
    header_bg.SetHeight(header_height)
    gump.Add(header_bg)
    title = API.CreateGumpLabel("🏠 THE ROOF", 1153)
    title.SetX(15)
    title.SetY(8)
    gump.Add(title)
    add_room_graphics(gump, "Roof")
    y, card_height = header_height + 15, 30
    for i, (boss_id, boss_name) in enumerate(ROOF_BOSS_NAMES.items()):
        create_modern_card(gump, 10, y, GUMP_CONFIG["Roof"]["w"] - 20, card_height)
        boss_label = API.CreateGumpLabel(f"💀 {boss_name} (ID: {boss_id}):", 1153)
        boss_label.SetX(20)
        boss_label.SetY(y + 8)
        gump.Add(boss_label)
        gump_controls["Roof"][f"boss_{boss_id}"] = API.CreateGumpLabel("WAITING", 1153)
        gump_controls["Roof"][f"boss_{boss_id}"].SetX(280)
        gump_controls["Roof"][f"boss_{boss_id}"].SetY(y + 8)
        gump.Add(gump_controls["Roof"][f"boss_{boss_id}"])
        y += card_height + 8
    create_modern_card(gump, 10, y, GUMP_CONFIG["Roof"]["w"] - 20, 40)
    gump_controls["Roof"]["room_status"] = API.CreateGumpLabel(
        "🎯 Waiting for first boss...", 1153
    )
    gump_controls["Roof"]["room_status"].SetX(20)
    gump_controls["Roof"]["room_status"].SetY(y + 12)
    gump.Add(gump_controls["Roof"]["room_status"])
    API.AddGump(gump)


def create_modern_belfry_gump():
    gump = create_modern_base_gump("Belfry")
    header_height = 35
    header_bg = API.CreateGumpColorBox(opacity=0.9, color=MODERN_COLORS["accent"])
    header_bg.SetWidth(GUMP_CONFIG["Belfry"]["w"])
    header_bg.SetHeight(header_height)
    gump.Add(header_bg)
    title = API.CreateGumpLabel("🔔 THE BELFRY", 1153)
    title.SetX(15)
    title.SetY(8)
    gump.Add(title)
    add_room_graphics(gump, "Belfry")
    y, card_height = header_height + 15, 50
    create_modern_card(gump, 10, y, GUMP_CONFIG["Belfry"]["w"] - 20, card_height)
    status_label = API.CreateGumpLabel("🎯 Room Status:", 1153)
    status_label.SetX(20)
    status_label.SetY(y + 8)
    gump.Add(status_label)
    gump_controls["Belfry"]["room_status"] = API.CreateGumpLabel(
        "Enter to begin...", 1153
    )
    gump_controls["Belfry"]["room_status"].SetX(20)
    gump_controls["Belfry"]["room_status"].SetY(y + 28)
    gump.Add(gump_controls["Belfry"]["room_status"])
    API.AddGump(gump)


def create_modern_bar_gump():
    gump = create_modern_base_gump("Bar")
    header_height = 35
    header_bg = API.CreateGumpColorBox(opacity=0.9, color=MODERN_COLORS["danger"])
    header_bg.SetWidth(GUMP_CONFIG["Bar"]["w"])
    header_bg.SetHeight(header_height)
    gump.Add(header_bg)
    title = API.CreateGumpLabel("🍺 BAR ROOM", 1153)
    title.SetX(15)
    title.SetY(8)
    gump.Add(title)
    add_room_graphics(gump, "Bar")
    y, card_height = header_height + 15, 30
    create_modern_card(gump, 10, y, GUMP_CONFIG["Bar"]["w"] - 20, card_height)
    gump_controls["Bar"]["bottles_thrown"] = create_stat_row_with_icon(
        gump, 20, y + 8, 0x099B, MODERN_ICONS["bottles"], "Bottles Thrown:", "0"
    )
    y += card_height + 8
    create_modern_card(gump, 10, y, GUMP_CONFIG["Bar"]["w"] - 20, card_height)
    gump_controls["Bar"]["enemies"] = create_stat_row(
        gump, 20, y + 8, MODERN_ICONS["enemies"], "Enemies in Range:", "0"
    )
    y += card_height + 8
    create_modern_card(gump, 10, y, GUMP_CONFIG["Bar"]["w"] - 20, card_height)
    gump_controls["Bar"]["bottles_available"] = create_stat_row_with_icon(
        gump, 20, y + 8, 0x099B, MODERN_ICONS["bottles"], "Bottles Available:", "0"
    )
    API.AddGump(gump)


def create_modern_orchard_gump():
    gump = create_modern_base_gump("Orchard")
    header_height = 35
    header_bg = API.CreateGumpColorBox(opacity=0.9, color=MODERN_COLORS["success"])
    header_bg.SetWidth(GUMP_CONFIG["Orchard"]["w"])
    header_bg.SetHeight(header_height)
    gump.Add(header_bg)
    title = API.CreateGumpLabel("🌳 ORCHARD ROOM", 1153)
    title.SetX(15)
    title.SetY(8)
    gump.Add(title)
    add_room_graphics(gump, "Orchard")
    y, card_height = header_height + 15, 30
    create_modern_card(gump, 10, y, GUMP_CONFIG["Orchard"]["w"] - 20, card_height)
    gump_controls["Orchard"]["pairs_completed"] = create_stat_row_with_icon(
        gump, 20, y + 8, 0x0D01, MODERN_ICONS["pairs"], "Pairs Completed:", "0 / 0"
    )
    y += card_height + 8
    create_modern_card(gump, 10, y, GUMP_CONFIG["Orchard"]["w"] - 20, card_height)
    gump_controls["Orchard"]["trees_found"] = create_stat_row_with_icon(
        gump, 20, y + 8, 0x0D01, MODERN_ICONS["pairs"], "Cypress Trees:", "0"
    )
    y += card_height + 8
    create_modern_card(gump, 10, y, GUMP_CONFIG["Orchard"]["w"] - 20, card_height)
    gump_controls["Orchard"]["apple_status"] = create_stat_row_with_icon(
        gump, 20, y + 8, 0x09D0, MODERN_ICONS["apple"], "Apple Status:", "..."
    )
    API.AddGump(gump)


def create_modern_armory_gump():
    gump = create_modern_base_gump("Armory")
    header_height = 35
    header_bg = API.CreateGumpColorBox(opacity=0.9, color=MODERN_COLORS["accent"])
    header_bg.SetWidth(GUMP_CONFIG["Armory"]["w"])
    header_bg.SetHeight(header_height)
    gump.Add(header_bg)
    title = API.CreateGumpLabel("⚔️ ARMORY ROOM", 1153)
    title.SetX(15)
    title.SetY(8)
    gump.Add(title)
    add_room_graphics(gump, "Armory")
    y, card_height = header_height + 15, 30
    stats_to_create = [
        (
            "phylacteries_purified",
            PHILACTERY_GRAPHIC,
            MODERN_ICONS["phylactery"],
            "Phylacteries Purified:",
            "0",
        ),
        (
            "armor_destroyed",
            CURSED_ARMOR_GRAPHIC,
            MODERN_ICONS["armor"],
            "Armor Destroyed:",
            "0",
        ),
        (
            "ground_phylacteries",
            PHILACTERY_GRAPHIC,
            MODERN_ICONS["phylactery"],
            "Ground Phylacteries:",
            "0",
        ),
        ("corrupt_in_bag", PHILACTERY_GRAPHIC, "💀", "Corrupt in Bag:", "0"),
        ("purified_in_bag", PHILACTERY_GRAPHIC, "✨", "Purified in Bag:", "0"),
        ("targets", FLAMES_GRAPHIC, MODERN_ICONS["flames"], "Flames / Armor:", "0 / 0"),
    ]
    for key, graphic_id, icon, label, value in stats_to_create:
        create_modern_card(gump, 10, y, GUMP_CONFIG["Armory"]["w"] - 20, card_height)
        gump_controls["Armory"][key] = create_stat_row_with_icon(
            gump, 20, y + 8, graphic_id, icon, label, value
        )
        y += card_height + 8
    API.AddGump(gump)


def create_modern_fountain_gump():
    gump = create_modern_base_gump("Fountain")
    header_height = 35
    header_bg = API.CreateGumpColorBox(opacity=0.9, color=MODERN_COLORS["warning"])
    header_bg.SetWidth(GUMP_CONFIG["Fountain"]["w"])
    header_bg.SetHeight(header_height)
    gump.Add(header_bg)
    title = API.CreateGumpLabel("💧 FOUNTAIN ROOM", 1153)
    title.SetX(15)
    title.SetY(8)
    gump.Add(title)
    add_room_graphics(gump, "Fountain")
    y, card_height = header_height + 15, 30
    create_modern_card(gump, 10, y, GUMP_CONFIG["Fountain"]["w"] - 20, card_height)
    gump_controls["Fountain"]["pieces_placed"] = create_stat_row_with_icon(
        gump, 20, y + 8, 0x9BE7, MODERN_ICONS["pieces"], "Pieces Placed:", "0"
    )
    y += card_height + 8
    create_modern_card(gump, 10, y, GUMP_CONFIG["Fountain"]["w"] - 20, card_height)
    gump_controls["Fountain"]["pieces_available"] = create_stat_row_with_icon(
        gump, 20, y + 8, 0x9BE7, MODERN_ICONS["pieces"], "Pieces Available:", "0"
    )
    y += card_height + 8
    create_modern_card(gump, 10, y, GUMP_CONFIG["Fountain"]["w"] - 20, card_height)
    gump_controls["Fountain"]["infrastructure"] = create_stat_row_with_icon(
        gump, 20, y + 8, 0x9BE5, MODERN_ICONS["fountain"], "Spigots / Drains:", "0 / 0"
    )
    API.AddGump(gump)


# --- UPDATE FUNCTIONS ---
def update_overview_gump():
    controls = gump_controls["Overview"]
    controls[
        "location"
    ].Text = f"{MODERN_ICONS['location']} Location: {current_stats['current_room']}"
    completed_rooms = sum(1 for completed in rooms_complete.values() if completed)
    for room, completed in rooms_complete.items():
        if f"status_{room.lower()}" in controls:
            controls[f"status_{room.lower()}"].Text = (
                f"{MODERN_ICONS['complete']} COMPLETE"
                if completed
                else f"{MODERN_ICONS['progress']} IN PROGRESS"
            )
    percent = int((completed_rooms / 6.0) * 100)
    controls[
        "overall_progress"
    ].Text = f"🎯 Overall Progress: {completed_rooms}/6 ({percent}%)"


def update_roof_gump():
    """
    UPDATED: Better roof gump that handles random boss spawning
    Also checks for remains to update boss status
    """
    global roof_current_boss_index
    controls = gump_controls["Roof"]

    # Always check for remains when updating
    check_boss_remains()

    # Check which bosses are currently active (spawned and alive)
    active_bosses = []
    for boss_id in ROOF_BOSS_IDS:
        if not roof_bosses_dead[boss_id]:
            boss_mobs = API.FindTypeAll(boss_id, range=30)
            if boss_mobs and boss_mobs[0].Hits > 0:
                active_bosses.append(boss_id)

    # Update individual boss statuses
    for boss_id, boss_name in ROOF_BOSS_NAMES.items():
        if f"boss_{boss_id}" in controls:
            if roof_bosses_dead[boss_id]:
                controls[f"boss_{boss_id}"].Text = "💀 DEAD"
            elif boss_id in active_bosses:
                controls[f"boss_{boss_id}"].Text = "⚔️ FIGHTING"
            else:
                controls[f"boss_{boss_id}"].Text = "⏳ WAITING"

    # Update room status
    dead_count = sum(1 for is_dead in roof_bosses_dead.values() if is_dead)
    if dead_count == len(ROOF_BOSS_IDS):
        controls[
            "room_status"
        ].Text = f"{MODERN_ICONS['complete']} All bosses defeated!"
        rooms_complete["Roof"] = True
    elif active_bosses:
        active_boss_names = [ROOF_BOSS_NAMES[bid] for bid in active_bosses]
        if len(active_bosses) == 1:
            controls[
                "room_status"
            ].Text = f"🎯 Fighting: {active_boss_names[0]} ({dead_count}/{len(ROOF_BOSS_IDS)})"
        else:
            controls[
                "room_status"
            ].Text = f"🎯 Fighting: {len(active_bosses)} bosses ({dead_count}/{len(ROOF_BOSS_IDS)})"
    else:
        controls[
            "room_status"
        ].Text = f"🎯 Waiting for next boss... ({dead_count}/{len(ROOF_BOSS_IDS)})"


def update_bar_gump():
    gump_controls["Bar"]["bottles_thrown"].Text = str(current_stats["bar_bottles_used"])
    gump_controls["Bar"]["enemies"].Text = str(
        len(API.NearestMobiles([API.Notoriety.Enemy, API.Notoriety.Murderer], 15))
    )
    gump_controls["Bar"]["bottles_available"].Text = str(
        len(API.FindTypeAll(0x099B, range=5))
    )


def update_orchard_gump():
    # Count cypress trees properly
    cypress_trees = []
    for tree in API.FindTypeAll(0x0D01, range=25):
        if "cypress" in API.ItemNameAndProps(tree.Serial, True).lower():
            cypress_trees.append(tree)

    tree_count = len(cypress_trees)
    total_pairs = tree_count // 2  # Integer division for proper pair count

    # Update gump controls
    pairs_completed = current_stats.get("orchard_pairs_complete", 0)
    gump_controls["Orchard"][
        "pairs_completed"
    ].Text = f"{pairs_completed} / {total_pairs}"
    gump_controls["Orchard"]["trees_found"].Text = str(tree_count)

    # Check apple status
    has_apple = API.FindType(0x09D0, API.Backpack) is not None
    gump_controls["Orchard"]["apple_status"].Text = (
        "Ready to throw!" if has_apple else "Need to pick apple"
    )


def update_armory_gump():
    controls = gump_controls["Armory"]
    backpack_items = API.ItemsInContainer(API.Backpack)
    controls["phylacteries_purified"].Text = str(
        current_stats["armory_phylacteries_purified"]
    )
    controls["armor_destroyed"].Text = str(current_stats["armory_armor_destroyed"])
    controls["ground_phylacteries"].Text = str(
        len(API.FindTypeAll(PHILACTERY_GRAPHIC, range=5))
    )
    controls["corrupt_in_bag"].Text = str(
        len(
            [
                i
                for i in backpack_items
                if i.Graphic == PHILACTERY_GRAPHIC and i.Hue == CORRUPT_PHYLACTERY_HUE
            ]
        )
    )
    controls["purified_in_bag"].Text = str(
        len(
            [
                i
                for i in backpack_items
                if i.Graphic == PHILACTERY_GRAPHIC and i.Hue == PURIFIED_PHYLACTERY_HUE
            ]
        )
    )
    flame_count = len(API.FindTypeAll(FLAMES_GRAPHIC, range=10))
    armor_count = len(
        API.FindTypeAll(CURSED_ARMOR_GRAPHIC, range=10)
        + API.FindTypeAll(CURSED_ARMOR_GRAPHIC_2, range=10)
    )
    controls["targets"].Text = f"{flame_count} / {armor_count}"


def update_fountain_gump():
    gump_controls["Fountain"]["pieces_placed"].Text = str(
        current_stats["fountain_pieces_placed"]
    )
    gump_controls["Fountain"]["pieces_available"].Text = str(
        sum(len(API.FindTypeAll(g, range=15)) for g in CANAL_PIECES.keys())
    )
    spigot_count = sum(len(API.FindTypeAll(g, range=15)) for g in SPIGOT_GRAPHICS)
    drain_count = len(API.FindTypeAll(DRAIN_GRAPHIC, range=15))
    gump_controls["Fountain"]["infrastructure"].Text = f"{spigot_count} / {drain_count}"


def update_belfry_gump():
    controls = gump_controls["Belfry"]
    if rooms_complete["Belfry"]:
        controls["room_status"].Text = f"{MODERN_ICONS['complete']} Room completed!"
    else:
        controls[
            "room_status"
        ].Text = f"{MODERN_ICONS['progress']} Fighting in progress..."


def update_active_gump():
    if active_gump_name == "None":
        return
    try:
        update_map = {
            "Overview": update_overview_gump,
            "Bar": update_bar_gump,
            "Orchard": update_orchard_gump,
            "Armory": update_armory_gump,
            "Fountain": update_fountain_gump,
            "Belfry": update_belfry_gump,
            "Roof": update_roof_gump,
        }
        if active_gump_name in update_map:
            update_map[active_gump_name]()
    except Exception:
        # API.SysMsg(f"Gump update error for {active_gump_name}: {e}", 33) # Optional: for debugging
        pass


def handle_orchard():
    global tree_partners, current_stats
    API.Pause(0.5)
    tree_partners.clear()
    tree_objects = []
    ignore2 = []
    picked = False
    picked_from_tree_serial = None
    pairs_completed = 0

    for tree in API.FindTypeAll(0x0D01, range=25):
        if "cypress" in API.ItemNameAndProps(tree.Serial).lower():
            tree_objects.append(tree)
    if len(tree_objects) < 2:
        return False

    tree_objects.sort(key=lambda t: t.Serial)
    pair_hues = [12, 44, 54, 64, 88, 98]
    pair_symbols = ["◆◆", "●●", "▲▲", "■■", "★★", "♦♦"]
    for i in range(0, len(tree_objects) - 1, 2):
        tree_A = tree_objects[i]
        tree_B = tree_objects[i + 1]
        hue = pair_hues[i // 2 % len(pair_hues)]
        symbol = pair_symbols[i // 2 % len(pair_symbols)]
        tree_partners[tree_A.Serial] = tree_B.Serial
        tree_partners[tree_B.Serial] = tree_A.Serial
        API.HeadMsg(f"{symbol} P{i // 2 + 1}", tree_A.Serial, hue)
        API.HeadMsg(f"{symbol} P{i // 2 + 1}", tree_B.Serial, hue)

    while not API.InJournal("You have bested this tower"):
        current_stats["orchard_pairs_complete"] = pairs_completed
        update_active_gump()

        # Show partner tree location if we have an apple
        if picked and picked_from_tree_serial in tree_partners:
            partner_obj = API.FindItem(tree_partners[picked_from_tree_serial])
            if partner_obj and partner_obj.Distance <= 8:
                API.HeadMsg("-> THROW <-", partner_obj.Serial, 77)
            elif partner_obj:
                API.HeadMsg("Too far", partner_obj.Serial, 44)

        # Pick apple if we don't have one
        if not picked:
            for tree in API.FindTypeAll(0x0D01, range=25):
                if (
                    tree.Serial in tree_partners
                    and tree.Serial not in ignore2
                    and tree.Distance < 4
                ):
                    API.UseObject(tree.Serial)
                    API.Pause(0.5)
                    if API.FindType(0x09D0, API.Backpack):
                        picked_from_tree_serial = tree.Serial
                        ignore2.append(tree.Serial)
                        picked = True
                        break

        # Throw apple at partner tree - ONLY when partner is close enough
        if picked and picked_from_tree_serial in tree_partners:
            partner_serial = tree_partners[picked_from_tree_serial]
            partner = API.FindItem(partner_serial)
            reagent = API.FindType(0x09D0, API.Backpack)

            if not reagent:
                picked = False
                picked_from_tree_serial = None
            elif partner and partner.Serial not in ignore2 and partner.Distance <= 8:
                # Partner is close enough - use apple and target
                API.UseObject(reagent.Serial)
                if API.WaitForTarget(timeout=1.5):
                    partner_recheck = API.FindItem(partner_serial)
                    if partner_recheck and partner_recheck.Distance <= 8:
                        API.Target(partner.Serial)
                        API.Pause(0.8)
                        if not API.FindType(0x09D0, API.Backpack):
                            ignore2.append(partner.Serial)
                            picked = False
                            picked_from_tree_serial = None
                            pairs_completed += 1
                            API.Pause(1.5)
                    else:
                        # Partner moved away, cancel if possible
                        if hasattr(API, "CancelTarget"):
                            API.CancelTarget()
            # If partner not close enough, just continue loop (don't use apple yet)

        elif picked and picked_from_tree_serial not in tree_partners:
            # Lost partner reference, reset
            picked = False
            picked_from_tree_serial = None

        API.Pause(0.5)

    # Clear all tree messages when done
    for tree in tree_objects:
        API.HeadMsg("", tree.Serial)
    return True


def handle_bar():
    # bottle = f['bottle'].get('Nearest')
    # if not bottle:
    #     return
    # Items.UseItem(bottle)
    # Target.WaitForTarget(500)
    # while Target.HasTarget():
    #     mob = f['pirate'].get('Nearest')
    #     if mob:
    #         Target.TargetExecute(mob)
    bottles_used = 0
    while not API.InJournal("You have bested this tower"):
        # These would be defined elsewhere in your script
        # current_stats["bar_bottles_used"] = bottles_used
        # update_active_gump()

        # --- SCAVENGER SYSTEM ---
        bottle_on_ground = API.FindType(0x099B, range=2)
        if not bottle_on_ground:
            continue

        API.UseObject(bottle_on_ground)
        API.WaitForTarget(timeout=0.5)
        while API.HasTarget():
            target = API.NearestMobile(
                [API.Notoriety.Enemy, API.Notoriety.Murderer], 10
            )
            if target:
                API.Target(target.Serial)
                bottles_used += 1
        API.Pause(0.2)

    return True


def handle_armory():
    phylacteries_purified, armor_destroyed, destroyed_armor = 0, 0, []
    while not API.InJournal("You have bested this tower"):
        current_stats["armory_phylacteries_purified"] = phylacteries_purified
        current_stats["armory_armor_destroyed"] = armor_destroyed
        update_active_gump()
        ground_phylactery = API.FindType(PHILACTERY_GRAPHIC, range=2)
        if ground_phylactery is not None:
            API.MoveItem(ground_phylactery.Serial, API.Backpack)
            API.Pause(0.3)
            continue
        flames = API.FindType(FLAMES_GRAPHIC, range=3)
        if flames is not None:
            backpack_items = API.ItemsInContainer(API.Backpack)
            corrupt_phylacteries = [
                item
                for item in backpack_items
                if item.Graphic == PHILACTERY_GRAPHIC
                and item.Hue == CORRUPT_PHYLACTERY_HUE
            ]
            for corrupt in corrupt_phylacteries:
                API.UseObject(corrupt.Serial)
                if API.WaitForTarget(timeout=1.0):
                    API.Target(flames.Serial)
                    phylacteries_purified += 1
                API.Pause(0.1)
        if API.HasTarget():
            API.Pause(0.1)
            continue
        backpack_items = API.ItemsInContainer(API.Backpack)
        purified_phylacteries = [
            item
            for item in backpack_items
            if item.Graphic == PHILACTERY_GRAPHIC
            and item.Hue == PURIFIED_PHYLACTERY_HUE
        ]
        if purified_phylacteries:
            for purified in purified_phylacteries:
                armor_statues = API.FindTypeAll(
                    CURSED_ARMOR_GRAPHIC, range=3
                ) + API.FindTypeAll(CURSED_ARMOR_GRAPHIC_2, range=3)
                available_armor = [
                    armor
                    for armor in armor_statues
                    if armor.Serial not in destroyed_armor
                ]
                if available_armor:
                    closest_armor = min(
                        available_armor,
                        key=lambda a: (
                            abs(safe_get_coords(a)[0] - API.Player.X)
                            + abs(safe_get_coords(a)[1] - API.Player.Y)
                        ),
                    )
                    API.UseObject(purified.Serial)
                    if API.WaitForTarget(timeout=1.0):
                        API.Target(closest_armor.Serial)
                        API.Pause(0.5)
                        remaining_purified = [
                            item
                            for item in API.ItemsInContainer(API.Backpack)
                            if item.Graphic == PHILACTERY_GRAPHIC
                            and item.Hue == PURIFIED_PHYLACTERY_HUE
                        ]
                        if len(remaining_purified) < len(purified_phylacteries):
                            armor_destroyed += 1
                            destroyed_armor.append(closest_armor.Serial)
                            API.SysMsg(f"Armor destroyed! Total: {armor_destroyed}", 77)
                        else:
                            API.SysMsg("Targeting failed - armor still there", 33)
                    else:
                        if hasattr(API, "CancelTarget"):
                            API.CancelTarget()
                    API.Pause(0.1)
        if get_current_room() != "Armory" and get_current_room() != "Unknown":
            break
        API.Pause(0.05)
    return True


def get_puzzle_template():
    return {piece: [] for piece in CANAL_PIECES.keys()}


def build_path(path_id, start, end, entry_point):
    global puzzle_path_locations
    current_pos = TriPoint(start.X, start.Y, start.Z)
    current_entry = entry_point
    iterations = 0
    while (current_pos.X != end.X or current_pos.Y != end.Y) and iterations < 50:
        iterations += 1
        piece_type = None
        next_pos = TriPoint(current_pos.X, current_pos.Y, current_pos.Z)
        if current_entry == "North":
            if current_pos.X < end.X:
                piece_type = 0x9BEF
                next_pos.X += 1
                current_entry = "West"
            elif current_pos.X == end.X:
                piece_type = 0x9BE7
                next_pos.Y += 1
                current_entry = "North"
            else:
                piece_type = 0x9BEB
                next_pos.X -= 1
                current_entry = "East"
        elif current_entry == "East":
            if current_pos.Y < end.Y:
                piece_type = 0x9BFC
                next_pos.Y += 1
                current_entry = "North"
            elif current_pos.Y == end.Y:
                piece_type = 0x9BF4
                next_pos.X -= 1
                current_entry = "East"
            else:
                piece_type = 0x9BEF
                next_pos.Y -= 1
                current_entry = "South"
        elif current_entry == "South":
            if current_pos.X < end.X:
                piece_type = 0x9BFC
                next_pos.X += 1
                current_entry = "West"
            elif current_pos.X == end.X:
                piece_type = 0x9BE7
                next_pos.Y -= 1
                current_entry = "South"
            else:
                piece_type = 0x9BF8
                next_pos.X -= 1
                current_entry = "East"
        elif current_entry == "West":
            if current_pos.Y < end.Y:
                piece_type = 0x9BF8
                next_pos.Y += 1
                current_entry = "North"
            elif current_pos.Y == end.Y:
                piece_type = 0x9BF4
                next_pos.X += 1
                current_entry = "West"
            else:
                piece_type = 0x9BEB
                next_pos.Y -= 1
                current_entry = "South"
        if piece_type:
            puzzle_path_locations[path_id][piece_type].append(current_pos)
            current_pos = next_pos
        else:
            break
    return iterations < 50


def is_piece_in_correct_position(piece):
    if piece.Graphic not in CANAL_PIECES:
        return True
    px, py, pz = safe_get_coords(piece)
    piece_pos = TriPoint(px, py, pz)
    for path_id in puzzle_path_locations:
        if piece_pos in puzzle_path_locations[path_id].get(piece.Graphic, []):
            return True
    return False


def handle_fountain():
    global puzzle_path_locations, current_stats
    API.Pause(1)
    API.ClearJournal()
    puzzle_path_locations.clear()
    for i in range(1, 5):
        puzzle_path_locations[i] = get_puzzle_template()
    spigots = []
    drains = []
    search_attempts = 0
    while (len(spigots) < 4 or len(drains) < 2) and search_attempts < 15:
        search_attempts += 1
        for graphic in SPIGOT_GRAPHICS:
            for spigot in API.FindTypeAll(graphic, range=20):
                if spigot.Serial not in [s.Serial for s in spigots]:
                    spigots.append(spigot)
        for drain in API.FindTypeAll(DRAIN_GRAPHIC, range=20):
            if drain.Serial not in [d.Serial for d in drains]:
                drains.append(drain)
        if len(spigots) < 4 or len(drains) < 2:
            API.Pause(3)
    if len(spigots) < 4 or len(drains) < 2:
        return False
    spigots_by_y = []
    spigots_by_x = []
    for spigot in spigots:
        sx, sy, sz = safe_get_coords(spigot)
        if len([s for s in spigots if abs(safe_get_coords(s)[1] - sy) <= 1]) > 1:
            spigots_by_y.append(spigot)
        else:
            spigots_by_x.append(spigot)
    spigots_by_y.sort(key=lambda s: safe_get_coords(s)[0])
    spigots_by_x.sort(key=lambda s: safe_get_coords(s)[1], reverse=True)
    path_id = 0
    for spigot in spigots_by_y:
        path_id += 1
        drain = min(drains, key=lambda d: safe_get_coords(d)[0])
        sx, sy, sz = safe_get_coords(spigot)
        dx, dy, dz = safe_get_coords(drain)
        build_path(path_id, TriPoint(sx, sy + 1, sz), TriPoint(dx, dy, dz), "North")
    for spigot in spigots_by_x:
        path_id += 1
        drain = min(drains, key=lambda d: safe_get_coords(d)[1])
        sx, sy, sz = safe_get_coords(spigot)
        dx, dy, dz = safe_get_coords(drain)
        build_path(path_id, TriPoint(sx + 1, sy, sz), TriPoint(dx, dy, dz), "West")
    loop_count = 0
    pieces_placed = 0
    while not API.InJournal("You have bested this tower") and loop_count < 500:
        loop_count += 1
        API.Pause(0.5)
        current_stats["fountain_pieces_placed"] = pieces_placed
        update_active_gump()
        incorrect_picked = False
        for piece in [
            p for g in CANAL_PIECES.keys() for p in API.FindTypeAll(g, range=2)
        ]:
            if not is_piece_in_correct_position(piece):
                API.MoveItem(piece.Serial, API.Backpack)
                API.Pause(0.4)
                incorrect_picked = True
                break
        if incorrect_picked:
            continue
        backpack_pieces = [
            p
            for p in API.ItemsInContainer(API.Backpack)
            if p.Graphic in CANAL_PIECES.keys()
        ]
        if backpack_pieces:
            occupied = set(
                (safe_get_coords(p)[0], safe_get_coords(p)[1])
                for g in CANAL_PIECES.keys()
                for p in API.FindTypeAll(g, range=25)
            )
            piece_placed = False
            for piece_to_place in backpack_pieces:
                if piece_placed:
                    break
                for path_id in puzzle_path_locations:
                    for pos in puzzle_path_locations[path_id].get(
                        piece_to_place.Graphic, []
                    ):
                        if (pos.X, pos.Y) in occupied:
                            continue
                        if abs(pos.X - API.Player.X) + abs(pos.Y - API.Player.Y) <= 2:
                            x_offset = pos.X - API.Player.X
                            y_offset = pos.Y - API.Player.Y
                            API.MoveItemOffset(
                                piece_to_place.Serial, 0, x_offset, y_offset, 0
                            )
                            pieces_placed += 1
                            API.Pause(0.6)
                            piece_placed = True
                            break
                    if piece_placed:
                        break
    return loop_count < 500


def handle_belfry():
    """Simple handler for Belfry room - just waits for completion"""
    while not API.InJournal("You have bested this tower"):
        update_active_gump()
        API.Pause(1)
    return True


def check_for_death():
    """Check if player has died and return to overview if so"""
    global last_player_hp, active_gump_name
    try:
        current_hp = API.Player.Hits
        if current_hp <= 0 and last_player_hp > 0:
            API.SysMsg("💀 Death detected - returning to overview", 33)
            if active_gump_name != "Overview":
                create_modern_overview_gump()
            current_stats["current_room"] = "Lobby"
        last_player_hp = current_hp
    except:
        pass


def check_boss_remains():
    """
    Check for boss remains to detect dead bosses
    Boss names in remains: "The Remains Of [BossName]"
    Updated with correct boss name mappings:
    - Ju'nar (ID: 33813) = "Juo'nar" in remains
    - Vial (ID: 2951) = "Ozymandias" in remains
    - Anon (ID: 1071) = "Anon" in remains
    - Virtuebane (ID: 33779) = "Virtuebane" in remains
    """
    global roof_bosses_dead

    # Check all corpses/remains in the area
    for item in API.FindTypeAll(0x2006, range=30):  # Corpse type
        try:
            item_name = API.ItemNameAndProps(item.Serial, True).lower()

            # Check for each boss's remains (with correct name mappings)
            if (
                "remains of ju'nar" in item_name
                or "remains of junar" in item_name
                or "remains of juo'nar" in item_name
            ):
                if not roof_bosses_dead[33813]:
                    roof_bosses_dead[33813] = True
                    API.SysMsg("💀 Detected Ju'nar's remains - marked as dead", 67)

            elif "remains of vial" in item_name or "remains of ozymandias" in item_name:
                if not roof_bosses_dead[2951]:
                    roof_bosses_dead[2951] = True
                    API.SysMsg(
                        "💀 Detected Vial/Ozymandias remains - marked as dead", 67
                    )

            elif "remains of anon" in item_name:
                if not roof_bosses_dead[1071]:
                    roof_bosses_dead[1071] = True
                    API.SysMsg("💀 Detected Anon's remains - marked as dead", 67)

            elif "remains of virtuebane" in item_name:
                if not roof_bosses_dead[33779]:
                    roof_bosses_dead[33779] = True
                    API.SysMsg("💀 Detected Virtuebane remains - marked as dead", 67)

        except:
            continue  # Skip if we can't read the item name


def handle_roof():
    """
    FIXED ROOF HANDLER: Handles random boss spawning order
    Detects whichever boss spawns and waits for it to die before continuing
    Also checks for boss remains to detect already dead bosses
    """
    global roof_bosses_dead, roof_current_boss_index

    API.ClearJournal()
    API.SysMsg("🏠 Roof encounter started. Checking for boss status...", 77)

    check_boss_remains()
    bosses_defeated = sum(1 for is_dead in roof_bosses_dead.values() if is_dead)
    total_bosses = len(ROOF_BOSS_IDS)

    if bosses_defeated > 0:
        API.SysMsg(f"📋 Found {bosses_defeated} already defeated bosses", 67)

    while bosses_defeated < total_bosses:
        if API.InJournal("You have bested this tower"):
            return True

        check_boss_remains()
        bosses_defeated = sum(1 for is_dead in roof_bosses_dead.values() if is_dead)

        current_active_boss = None
        current_active_boss_id = None

        # --- START OF CORRECTION ---
        # Get all mobiles the client can see instead of using FindTypeAll
        all_mobiles = API.GetAllMobiles()

        for boss_id in ROOF_BOSS_IDS:
            if not roof_bosses_dead[boss_id]:
                # Now, loop through the mobiles to find a match
                for mob in all_mobiles:
                    # Check if the mobile's graphic matches the boss ID, it's alive, and nearby
                    if mob.Graphic == boss_id and mob.Hits > 0 and mob.Distance < 30:
                        current_active_boss = mob
                        current_active_boss_id = boss_id
                        break  # Found the active boss, stop searching mobiles
            if current_active_boss:
                break  # Stop searching boss IDs
        # --- END OF CORRECTION ---

        if current_active_boss is not None:
            boss_name = ROOF_BOSS_NAMES.get(
                current_active_boss_id, f"Boss {current_active_boss_id}"
            )
            API.SysMsg(f"⚔️ {boss_name} is active! Waiting for defeat...", 44)

            while True:
                if API.InJournal("You have bested this tower"):
                    return True

                check_boss_remains()
                if roof_bosses_dead[current_active_boss_id]:
                    bosses_defeated += 1
                    API.SysMsg(
                        f"✅ {boss_name} defeated! ({bosses_defeated}/{total_bosses})",
                        77,
                    )
                    # update_active_gump() # Assumed to be defined elsewhere
                    API.Pause(2.0)
                    break

                roof_current_boss_index = list(ROOF_BOSS_IDS).index(
                    current_active_boss_id
                )
                # update_active_gump() # Assumed to be defined elsewhere
                API.Pause(0.5)
        else:
            API.Pause(1.0)
            # update_active_gump() # Assumed to be defined elsewhere

    API.SysMsg("🎉 All roof bosses defeated! Room complete!", 77)
    # rooms_complete["Roof"] = True # Assumed to be defined elsewhere
    # update_active_gump() # Assumed to be defined elsewhere
    return True


# --- MAIN SCRIPT LOOP ---
API.ClearJournal()
API.SysMsg("🚀 Enhanced Shadowguard UI - Initialized", 77)
load_gump_positions()
create_modern_overview_gump()

try:
    while True:
        API.Pause(0.1)
        API.ProcessCallbacks()
        gumps_to_check = list(_open_gump_instances.items())
        positions_changed = False
        gumps_to_remove = []
        for gump_name, gump_obj in gumps_to_check:
            try:
                current_gump_x, current_gump_y = (
                    int(gump_obj.GetX()),
                    int(gump_obj.GetY()),
                )
                if (
                    GUMP_CONFIG[gump_name]["x"] != current_gump_x
                    or GUMP_CONFIG[gump_name]["y"] != current_gump_y
                ):
                    GUMP_CONFIG[gump_name]["x"] = current_gump_x
                    GUMP_CONFIG[gump_name]["y"] = current_gump_y
                    positions_changed = True
            except:
                gumps_to_remove.append(gump_name)
        for name_to_remove in gumps_to_remove:
            if name_to_remove in _open_gump_instances:
                del _open_gump_instances[name_to_remove]
        if positions_changed:
            save_gump_positions()

        current_room = get_current_room()
        current_stats["current_room"] = current_room
        check_for_death()
        target_gump_name = (
            current_room
            if current_room != "Lobby" and not rooms_complete.get(current_room, False)
            else "Overview"
        )

        if active_gump_name != target_gump_name:
            if target_gump_name == "Overview":
                create_modern_overview_gump()
            elif target_gump_name == "Bar":
                create_modern_bar_gump()
            elif target_gump_name == "Orchard":
                create_modern_orchard_gump()
            elif target_gump_name == "Armory":
                create_modern_armory_gump()
            elif target_gump_name == "Fountain":
                create_modern_fountain_gump()
            elif target_gump_name == "Belfry":
                create_modern_belfry_gump()
            elif target_gump_name == "Roof":
                create_modern_roof_gump()

        update_active_gump()

        if current_room != "Lobby" and not rooms_complete.get(current_room, False):
            API.ClearJournal()
            success = False
            if current_room == "Fountain":
                success = handle_fountain()
            elif current_room == "Armory":
                success = handle_armory()
            elif current_room == "Orchard":
                success = handle_orchard()
            elif current_room == "Bar":
                success = handle_bar()
            elif current_room == "Belfry":
                success = handle_belfry()
            elif current_room == "Roof":
                success = handle_roof()
            if success or API.InJournal("You have bested this tower"):
                if not rooms_complete.get(current_room, False):
                    rooms_complete[current_room] = True
                    API.SysMsg(f"🎉 {current_room} COMPLETED! 🎉", 77)

        if all(rooms_complete.values()):
            API.HeadMsg("🎉 ALL SHADOWGUARD ROOMS COMPLETE! 🎉", API.Player.Serial, 77)
            close_all_gumps()
            API.Stop()
            break
finally:
    API.SysMsg("💾 Saving final UI positions...", 67)
    close_all_gumps()
    API.Stop()
