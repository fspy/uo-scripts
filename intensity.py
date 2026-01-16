import re
from typing import Optional
from urllib.parse import urlencode

import API
from _lib.pet_parser import LORE_GUMP_ID

BASEFONT_PATTERN = r"<BASEFONT[^>]*>([^<]*)</BASEFONT>"

STAT_RE = re.compile(
    r"<div align=right>(\d+(?:\.\d+)?)(?:/\d+)?%?</div>", re.IGNORECASE
)

RESIST_RE = re.compile(
    r"(?:<BASEFONT[^>]*>)?<div align=right>(\d+(?:\.\d+)?)(?:/\d+)?%?</div>",
    re.IGNORECASE,
)

CENTER_BASEFONT_PATTERN = (
    r"<CENTER><BASEFONT[^>]*>(?:<h4>)?([^<]*)(?:</h4>)?</BASEFONT></CENTER>"
)

INTENSITY_WEIGHTS = {
    "str": 3.0,
    "hits": 3.0,
    "dex": 0.1,
    "int": 0.5,
    "stam": 0.5,
    "mana": 0.5,
    "phys_res": 3.0,
    "fire_res": 3.0,
    "cold_res": 3.0,
    "poison_res": 3.0,
    "energy_res": 3.0,
}

INTENSITY_RANGES = {
    "CuSidhe": {
        "Wild": (4624, 5261),
        "Tamed": (4329, 4966),
    },
}

RESIST_COLORS = {
    "phys": "#DC7633",
    "fire": "#FF0000",
    "cold": "#00FFFF",
    "poison": "#00FF00",
    "energy": "#FF00FF",
}

STATS_PRIMARY = [("str", "Str"), ("dex", "Dex"), ("int", "Int")]
STATS_SECONDARY = [("hits", "Hits"), ("stam", "Stam"), ("mana", "Mana")]
RESISTS = [
    ("phys_res", "Phys"),
    ("fire_res", "Fire"),
    ("cold_res", "Cold"),
    ("poison_res", "Poison"),
    ("energy_res", "Energy"),
]


def parse_gump(html: str) -> Optional[dict]:
    basefont_matches = re.findall(BASEFONT_PATTERN, html, re.IGNORECASE)

    if len(basefont_matches) < 2:
        return None

    animal_class = basefont_matches[1]

    if (
        len(basefont_matches) > 2
        and basefont_matches[2].strip() == "Tame before bonding"
    ):
        animal_status = "Wild"
    else:
        animal_status = "Tamed"

    matches = list(re.finditer(CENTER_BASEFONT_PATTERN, html, re.IGNORECASE))
    str_index = next(
        (i for i, m in enumerate(matches) if m.group(1).strip() == "Str"), -1
    )

    if str_index == -1 or len(matches) < str_index + 18:
        return None

    stat_matches = matches[str_index : str_index + 18]
    stats = {}

    for i in range(3):
        base_idx = i * 6
        value1 = stat_matches[base_idx + 3].group(1).strip()
        value2_full = stat_matches[base_idx + 4].group(1).strip()
        value2_match = STAT_RE.search(value2_full)
        value2_max = (
            value2_match.group(1)
            if value2_match
            else value2_full.split("/")[1]
            if "/" in value2_full
            else value2_full
        )

        if i == 0:
            stats["str"] = value1
            stats["hits"] = value2_max
        elif i == 1:
            stats["dex"] = value1
            stats["stam"] = value2_max
        elif i == 2:
            stats["int"] = value1
            stats["mana"] = value2_max

    for resist_type, color in RESIST_COLORS.items():
        pattern = rf"COLOR={color}>(.*?)(?=COLOR=#|$)"
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            resist_value_raw = match.group(1)
            resist_match = RESIST_RE.search(resist_value_raw)
            resist_value = resist_match.group(1) if resist_match else resist_value_raw
            stats[resist_type + "_res"] = resist_value

    return {
        "class": animal_class,
        "status": animal_status,
        "stats": stats,
    }


STAT_HALF_ON_TAME = {
    "str": 2.0,
    "hits": 2.0,
    "dex": 2.0,
    "stam": 2.0,
}


def calculate_intensity(stats: dict, pet_status: str) -> float:
    total = 0.0
    for key, weight in INTENSITY_WEIGHTS.items():
        if key in stats and stats[key]:
            try:
                val = float(stats[key])
                if pet_status == "Wild" and key in STAT_HALF_ON_TAME:
                    val = val / STAT_HALF_ON_TAME[key]
                total += val * weight
            except (ValueError, TypeError):
                pass
    return total


def calculate_rating(intensity: float, pet_class: str, status: str) -> float:
    if pet_class not in INTENSITY_RANGES:
        return 0.0
    if status not in INTENSITY_RANGES[pet_class]:
        return 0.0
    min_val, max_val = INTENSITY_RANGES[pet_class][status]
    return max(0.0, min(100.0, (intensity - min_val) / (max_val - min_val) * 100))


try:
    from urllib.parse import urlencode
    from urllib.request import urlopen

    def query_uocah_rating(stats: dict) -> Optional[float]:
        """Query uo-cah for intensity rating based on pet stats."""
        creature_map = {
            "CuSidhe": "Cu+Sidhe",
        }

        creature_name = stats.get("class", "CuSidhe")
        creature = creature_map.get(creature_name, creature_name.replace(" ", "+"))

        params = {
            "creature": creature,
            "hits": stats.get("hits", 0),
            "stamina": stats.get("stam", 0),
            "mana": stats.get("mana", 0),
            "str": stats.get("str", 0),
            "dex": stats.get("dex", 0),
            "int": stats.get("int", 0),
            "rateminimum": 1,
            "physical": stats.get("phys_res", 0),
            "fire": stats.get("fire_res", 0),
            "cold": stats.get("cold_res", 0),
            "poison": stats.get("poison_res", 0),
            "energy": stats.get("energy_res", 0),
            "target_physical": "--",
            "target_fire": "--",
            "target_cold": "--",
            "target_poison": "--",
            "target_energy": "--",
            "wrestling": "",
            "resistingspells": "",
            "evalintel": "",
            "tactics": "",
            "magery": "",
            "poisoning": "",
            "mic": "fresh",
        }

        url = f"https://www.uo-cah.com/pet-intensity-calculator?{urlencode(params)}#freshresults"

        try:
            with urlopen(url, timeout=5) as response:
                html = response.read().decode("utf-8")
                rating_match = re.search(r"Rating:\s*(\d+(?:\.\d+)?)\s*%", html)
                if rating_match:
                    return float(rating_match.group(1))
        except Exception:
            pass

        return None

except ImportError:

    def query_uocah_rating(stats: dict) -> Optional[float]:
        return None


def main():
    if API.HasGump(LORE_GUMP_ID):
        API.SysMsg("Closing existing gump...")
        API.CloseGumps()

    API.HeadMsg("Select an Animal", API.Player)
    API.UseSkill("Animal Lore")

    if not API.WaitForGump(LORE_GUMP_ID, 30):
        API.SysMsg("No gump opened", 33)
        API.Stop()
        return

    html = API.GetGumpContents(LORE_GUMP_ID)
    result = parse_gump(html)

    if not result:
        API.SysMsg("Failed to parse gump", 33)
        API.Stop()
        return

    stats = result["stats"]

    if result["class"] not in INTENSITY_RANGES:
        API.SysMsg(f"[{result['class']}] {result['status']} - No intensity data")
        return

    uocah_rating = query_uocah_rating(stats)

    if uocah_rating is not None:
        rating = uocah_rating
        rating_display = f"{rating:.1f}%"
        intensity = None
        API.SysMsg(
            f"[{result['class']}] {result['status']} - {rating_display} (uo-cah)"
        )
    else:
        intensity = calculate_intensity(stats, result["status"])
        rating = calculate_rating(intensity, result["class"], result["status"])
        rating_display = f"{rating:.1f}%"
        min_int, max_int = INTENSITY_RANGES[result["class"]][result["status"]]
        API.SysMsg(
            f"[{result['class']}] {result['status']} - {rating_display} (Intensity: {intensity:.0f} / {min_int}-{max_int})"
        )

    if rating >= 70:
        API.HeadMsg(f" NICE PET: {rating_display}", API.Player)

    line1_parts = []
    for key, label in STATS_PRIMARY:
        val = stats.get(key, "N/A")
        line1_parts.append(f"{label}: {val}")
    API.SysMsg(" | ".join(line1_parts))

    line2_parts = []
    for key, label in STATS_SECONDARY:
        val = stats.get(key, "N/A")
        line2_parts.append(f"{label}: {val}")
    API.SysMsg(" | ".join(line2_parts))

    line3_parts = []
    for key, label in RESISTS:
        val = stats.get(key, "N/A")
        line3_parts.append(f"{label}: {val}")
    API.SysMsg(" | ".join(line3_parts))


def monitor():
    API.SysMsg("Pet monitor started - press Escape to stop")
    while not API.StopRequested:
        if API.HasGump(LORE_GUMP_ID):
            API.Pause(0.3)
            html = API.GetGumpContents(LORE_GUMP_ID)
            result = parse_gump(html)
            if result:
                stats = result["stats"]

                if result["class"] not in INTENSITY_RANGES:
                    API.SysMsg(
                        f"[{result['class']}] {result['status']} - No intensity data"
                    )
                else:
                    uocah_rating = query_uocah_rating(stats)

                    if uocah_rating is not None:
                        rating = uocah_rating
                        rating_display = f"{rating:.1f}%"
                        intensity = None
                        API.SysMsg(
                            f"[{result['class']}] {result['status']} - {rating_display} (uo-cah)"
                        )
                    else:
                        intensity = calculate_intensity(stats, result["status"])
                        rating = calculate_rating(
                            intensity, result["class"], result["status"]
                        )
                        rating_display = f"{rating:.1f}%"
                        min_int, max_int = INTENSITY_RANGES[result["class"]][
                            result["status"]
                        ]
                        API.SysMsg(
                            f"[{result['class']}] {result['status']} - {rating_display} (Intensity: {intensity:.0f} / {min_int}-{max_int})"
                        )

                    if rating >= 70:
                        API.HeadMsg(f" NICE PET: {rating_display}", API.Player)

                    line1_parts = []
                    for key, label in STATS_PRIMARY:
                        val = stats.get(key, "N/A")
                        line1_parts.append(f"{label}: {val}")
                    API.SysMsg(" | ".join(line1_parts))

                    line2_parts = []
                    for key, label in STATS_SECONDARY:
                        val = stats.get(key, "N/A")
                        line2_parts.append(f"{label}: {val}")
                    API.SysMsg(" | ".join(line2_parts))

                    line3_parts = []
                    for key, label in RESISTS:
                        val = stats.get(key, "N/A")
                        line3_parts.append(f"{label}: {val}")
                    API.SysMsg(" | ".join(line3_parts))
        API.Pause(0.2)


main()
