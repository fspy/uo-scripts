import re
from typing import Optional

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

    intensity = calculate_intensity(stats, result["status"])
    rating = calculate_rating(intensity, result["class"], result["status"])

    rating_display = f"{rating:.1f}%"
    min_int, max_int = INTENSITY_RANGES[result["class"]][result["status"]]

    if rating >= 70:
        API.HeadMsg(f" NICE PET: {rating_display}", API.Player)

    API.SysMsg(
        f"[{result['class']}] {result['status']} - {rating_display} (Intensity: {intensity:.0f} / {min_int}-{max_int})"
    )

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
                    intensity = calculate_intensity(stats, result["status"])
                    rating = calculate_rating(
                        intensity, result["class"], result["status"]
                    )
                    rating_display = f"{rating:.1f}%"
                    min_int, max_int = INTENSITY_RANGES[result["class"]][
                        result["status"]
                    ]

                    if rating >= 70:
                        API.HeadMsg(f" NICE PET: {rating_display}", API.Player)

                    API.SysMsg(
                        f"[{result['class']}] {result['status']} - {rating_display} (Intensity: {intensity:.0f} / {min_int}-{max_int})"
                    )

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
