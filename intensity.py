import re
from typing import Optional
from urllib.parse import urlencode
from urllib.request import urlopen

import API
from _lib.utils import p

LORE_GUMP_ID = 0x772051E9

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

RESIST_COLORS = {
    "phys": "#DC7633",
    "fire": "#FF0000",
    "cold": "#00FFFF",
    "poison": "#00FF00",
    "energy": "#FF00FF",
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
        "halves_on_tame": clean_pet_name(animal_class) in HALF_STAT_PETS,
    }


SUPPORTED_PETS = {
    "CuSidhe": "Cu+Sidhe",
}

HALF_STAT_PETS = {"CuSidhe"}

NAME_PREFIXES = {
    "Uncommon",
    "Rare",
    "Epic",
    "Legendary",
}


def clean_pet_name(name: str) -> str:
    for prefix in NAME_PREFIXES:
        if name.startswith(prefix + " "):
            name = name[len(prefix) + 1 :]
    return name.strip()


def query_uocah_rating(result: dict) -> Optional[float]:
    """Query uo-cah for intensity rating based on pet stats."""
    creature_name = result.get("class", "")
    stats = result.get("stats", {})
    pet_status = result.get("status", "")
    halves_on_tame = result.get("halves_on_tame", False)

    def get_val(key):
        val = int(stats.get(key, 0))
        if (
            pet_status == "Wild"
            and halves_on_tame
            and key in ("str", "hits", "dex", "stam")
        ):
            val = val // 2
        return max(125, val)

    # Clean rarity prefixes for uo-cah
    clean_name = clean_pet_name(creature_name)
    creature = SUPPORTED_PETS.get(clean_name, SUPPORTED_PETS.get(creature_name))

    p(creature)

    if not creature:
        API.SysMsg(f"[{creature_name}] - Unsupported pet type")
        return None

    params = {
        "hits": get_val("hits"),
        "stamina": get_val("stam"),
        "mana": stats.get("mana", 0),
        "str": get_val("str"),
        "dex": get_val("dex"),
        "int": stats.get("int", 0),
        "rateminimum": 1,
        "physical": stats.get("phys_res", 0),
        "fire": stats.get("fire_res", 0),
        "cold": stats.get("cold_res", 0),
        "poison": stats.get("poison_res", 0),
        "energy": stats.get("energy_res", 0),
        "target_physical": "--",
        "target_fire": "--",
        "target_cold": "70",
        "target_poison": "--",
        "target_energy": "75",
        "wrestling": "100",
        "resistingspells": "100",
        "evalintel": "",
        "tactics": "100",
        "magery": "",
        "poisoning": "",
        "mic": "fresh",
    }

    url = f"https://www.uo-cah.com/pet-intensity-calculator?creature={creature}&{urlencode(params)}#freshresults"
    try:
        with urlopen(url, timeout=10) as response:
            html = response.read().decode("utf-8")
            rating_match = re.search(
                r"Intensity Rating:\s*<strong>([\d.]+)%?</strong>", html
            )
            if rating_match:
                rating = float(rating_match.group(1))
                return rating
            else:
                API.SysMsg("uo-cah: Could not parse rating", 33)
    except Exception as e:
        API.SysMsg(f"uo-cah request failed: {e}", 33)

    return None


def main():
    if API.HasGump(LORE_GUMP_ID):
        API.SysMsg("Closing existing gump...")
        API.CloseGumps()

    API.UseSkill("Animal Lore")
    API.HeadMsg("Select an Animal", API.Player)

    if not API.WaitForGump(LORE_GUMP_ID, 3):
        API.SysMsg("No gump opened", 33)
        API.Stop()
        return

    html = API.GetGumpContents(LORE_GUMP_ID)
    result = parse_gump(html)

    if not result:
        API.SysMsg("Failed to parse gump", 33)
        API.Stop()
        return

    pet_class = clean_pet_name(result["class"])
    pet_status = result["status"]

    rating = query_uocah_rating(result)

    if rating is None:
        API.SysMsg("Could not get rating from uo-cah", 33)
        API.Stop()
        return

    rating_display = f"{rating:.1f}%"
    API.HeadMsg(f"Rating: {rating_display}", API.Player, 69 if rating >= 70 else 33)
    API.SysMsg(f"[{pet_class}] {pet_status} - {rating_display}")


main()
