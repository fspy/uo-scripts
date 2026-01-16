import re
from typing import Optional, Tuple

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

RANGES = {
    "CuSidhe": {
        "Wild": {
            "hits": (1000, 1200),
            "stam": (150, 170),
            "mana": (250, 290),
            "str": (1200, 1225),
            "dex": (150, 170),
            "int": (250, 290),
            "phys_res": (50, 65),
            "fire_res": (25, 45),
            "cold_res": (70, 85),
            "poison_res": (30, 50),
            "energy_res": (70, 85),
        },
        "Tamed": {
            "hits": (500, 600),
            "stam": (75, 85),
            "mana": (250, 290),
            "str": (600, 612),
            "dex": (75, 85),
            "int": (250, 290),
            "phys_res": (50, 65),
            "fire_res": (25, 45),
            "cold_res": (70, 85),
            "poison_res": (30, 50),
            "energy_res": (70, 85),
        },
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

SOFT_CAPS = {
    "cold_res": 70,
    "energy_res": 70,
}


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


def evaluate(
    stats: dict, pet_class: str, pet_status: str, ranges: dict
) -> Tuple[dict, float]:
    pet_ranges = ranges.get(pet_class, {})
    status_ranges = pet_ranges.get(pet_status, {})

    evaluation = {}
    total_percentile = 0
    count = 0

    for key, (min_val, max_val) in status_ranges.items():
        val = stats.get(key)
        if val and max_val > min_val:
            val_int = int(val.strip("%") or 0)
            percentile = max(
                0, min(100, (val_int - min_val) / (max_val - min_val) * 100)
            )

            soft_cap = SOFT_CAPS.get(key)
            if soft_cap is not None and val_int > soft_cap:
                over_amount = val_int - soft_cap
                penalty = (over_amount**2) * 2
                percentile = max(0, percentile - penalty)

            evaluation[key] = f"{val} ({percentile:.0f}%)"
            total_percentile += percentile
            count += 1
        else:
            evaluation[key] = f"{stats.get(key, 'N/A')} (N/A%)"

    avg_percentile = total_percentile / count if count > 0 else 0
    return evaluation, avg_percentile


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

    if result["class"] not in RANGES:
        API.SysMsg(f"[{result['class']}] {result['status']} - No ranges defined")
        return

    evaluation, avg = evaluate(stats, result["class"], result["status"], RANGES)

    avg_display = f"{avg:.1f}%"
    stat_count = len([k for k in evaluation.keys() if "_res" not in k])

    if avg >= 70:
        API.HeadMsg(f" NICE PET: {avg_display}", API.Player)

    API.SysMsg(
        f"[{result['class']}] {result['status']} - {avg_display} ({stat_count} stats)"
    )

    line1_parts = []
    for key, label in STATS_PRIMARY:
        line1_parts.append(f"{label}: {evaluation.get(key, 'N/A')}")
    API.SysMsg(" | ".join(line1_parts))

    line2_parts = []
    for key, label in STATS_SECONDARY:
        line2_parts.append(f"{label}: {evaluation.get(key, 'N/A')}")
    API.SysMsg(" | ".join(line2_parts))

    line3_parts = []
    for key, label in RESISTS:
        line3_parts.append(f"{label}: {evaluation.get(key, 'N/A')}")
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
                evaluation, avg = evaluate(
                    stats, result["class"], result["status"], RANGES
                )
                avg_display = f"{avg:.1f}%"
                stat_count = len([k for k in evaluation.keys() if "_res" not in k])
                API.SysMsg(
                    f"[{result['class']}] {result['status']} - {avg_display} ({stat_count} stats)"
                )
                line1_parts = []
                for key, label in STATS_PRIMARY:
                    line1_parts.append(f"{label}: {evaluation.get(key, 'N/A')}")
                API.SysMsg(" | ".join(line1_parts))
                line2_parts = []
                for key, label in STATS_SECONDARY:
                    line2_parts.append(f"{label}: {evaluation.get(key, 'N/A')}")
                API.SysMsg(" | ".join(line2_parts))
                line3_parts = []
                for key, label in RESISTS:
                    line3_parts.append(f"{label}: {evaluation.get(key, 'N/A')}")
                API.SysMsg(" | ".join(line3_parts))
        API.Pause(0.2)


main()
