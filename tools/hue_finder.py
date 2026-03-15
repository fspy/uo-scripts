import subprocess
import time

import API
from _lib.utils import Hue, p


def get_average_rgb(geometry):
    grim_proc = subprocess.Popen(
        ["grim", "-g", geometry, "-"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    magick_proc = subprocess.Popen(
        ["magick", "-", "-format", "%c", "histogram:"],
        stdin=grim_proc.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    grim_proc.stdout.close()
    output, _ = magick_proc.communicate()

    if not output:
        return None

    total_r = 0
    total_g = 0
    total_b = 0
    total_count = 0

    try:
        text = output.decode("utf-8", errors="ignore")
    except Exception:
        return None

    for line in text.strip().split("\n"):
        line = line.strip()
        if not line or ":" not in line:
            continue
        try:
            parts = line.split(":")
            count = int(parts[0].strip())
            color_part = parts[1].strip().split("#")[0].strip().lstrip("(").rstrip(")")
            r, g, b = map(int, color_part.split(","))

            brightness = (r + g + b) / 3
            if brightness < 25:
                continue

            total_r = total_r + (r * count)
            total_g = total_g + (g * count)
            total_b = total_b + (b * count)
            total_count = total_count + count
        except Exception:
            continue

    if total_count == 0:
        return None

    return (total_r / total_count, total_g / total_count, total_b / total_count)


def color_distance(c1, c2):
    dr = c1[0] - c2[0]
    dg = c1[1] - c2[1]
    db = c1[2] - c2[2]
    return (dr * dr + dg * dg + db * db) ** 0.5


def main():
    p("=== Hue Finder (Average RGB) ===", Hue.Cyan)

    p("Step 1: Target craftable wall object", Hue.Yellow)
    craft_serial = API.RequestTarget(timeout=30)
    if not craft_serial:
        p("No target", Hue.Red)
        return
    craft_obj = API.FindItem(craft_serial)
    if not craft_obj:
        p("Invalid target", Hue.Red)
        return
    p(f"Target: {craft_obj.Name}", Hue.Green)

    ref_geometry = "584,386 55x165"
    craft_geometry = "521,445 55x165"

    p("Step 2: Capturing reference...", Hue.Yellow)
    ref_avg = get_average_rgb(ref_geometry)
    if not ref_avg:
        p("Failed to capture reference", Hue.Red)
        return
    p(f"Ref color: {ref_avg[0]:.1f}, {ref_avg[1]:.1f}, {ref_avg[2]:.1f}", Hue.Green)

    p("\n=== Scanning hues 1-2999 ===", Hue.Cyan)
    p("Press ESC to stop", Hue.Gray)

    bad_ranges = [
        (1133, 1133),
        (1141, 1141),
        (1149, 1149),
        (1156, 1157),
        (1193, 1194),
        (1198, 1199),
        (1267, 1267),
        (1279, 1280),
        (1295, 1295),
        (1367, 1367),
        (1460, 1461),
        (1464, 1464),
        (1483, 1487),
        (1570, 1570),
        (1665, 1672),
        (1684, 1684),
        (1699, 1699),
        (1765, 1765),
        (1770, 1771),
        (1775, 1776),
        (1780, 1800),
        (1909, 1909),
        (1998, 2000),
        (2049, 2057),
        (2068, 2068),
        (2073, 2074),
        (2077, 2100),
        (2131, 2200),
        (2225, 2300),
        (2319, 2400),
        (2431, 2497),
        (2645, 2650),
        (2663, 2670),
        (2719, 2719),
        (2722, 2724),
        (2726, 2726),
        (2749, 2750),
        (2752, 2753),
        (2765, 2765),
        (2772, 2772),
        (2776, 2776),
        (2779, 2779),
        (2785, 2946),
        (2948, 2948),
        (2950, 2950),
        (2954, 2954),
        (2957, 2957),
        (2971, 2999),
    ]

    def is_bad_hue(h):
        for start, end in bad_ranges:
            if start <= h <= end:
                return True
        return False

    results = []
    best_dist = 999999
    best_hue = None

    for hue_num in range(1, 3000):
        if is_bad_hue(hue_num):
            continue

        if hue_num % 100 == 0:
            p(f"Hue {hue_num} best={best_hue}", Hue.White)

        craft_obj.SetHue(hue_num)
        time.sleep(0.01)

        craft_avg = get_average_rgb(craft_geometry)
        if not craft_avg:
            p(f"Hue {hue_num}: capture failed", Hue.Red)
            continue

        dist = color_distance(ref_avg, craft_avg)
        results.append((hue_num, dist))

        if dist < best_dist:
            best_dist = dist
            best_hue = hue_num
            p(f"Hue {hue_num}: dist={dist} **BEST**", Hue.Green)

    p("\n=== RESULTS ===", Hue.Cyan)
    for i, (h, d) in enumerate(sorted(results, key=lambda x: x[1])[:10], 1):
        p(f"  {i}. Hue {h} (0x{h:04X}): {d}", Hue.Yellow)

    p(f"\nBest: Hue {best_hue} (0x{best_hue:04X})", Hue.Green)
    p(f"Apply: craft_obj.SetHue({best_hue})", Hue.Cyan)
    craft_obj.SetHue(best_hue)


main()
