import json
import time
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

LOG_FILE = Path(__file__).parent.parent / "gathering" / "resource_log.json"


def _load_log() -> dict:
    """Load the resource log from disk. Returns empty dict if file doesn't exist."""
    if not LOG_FILE.exists():
        return {"mining": [], "lumberjacking": []}

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except IOError:
        return {"mining": [], "lumberjacking": []}


def _save_log(data: dict) -> None:
    """Save the resource log to disk with retry logic for concurrent access."""
    max_retries = 5
    for attempt in range(max_retries):
        try:
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return
        except IOError as _:
            if attempt < max_retries - 1:
                time.sleep(0.1 * (attempt + 1))
            else:
                raise


def log_mining_gather(
    player_x: int,
    player_y: int,
    player_z: int,
    offset_x: int,
    offset_y: int,
    runebook_index: int,
    material: str,
) -> None:
    """Log a successful mining gather of colored ore.

    Args:
        player_x: Player's X position at time of mining
        player_y: Player's Y position at time of mining
        player_z: Player's Z position at time of mining
        offset_x: X offset from player (from MINE_OFFSETS)
        offset_y: Y offset from player (from MINE_OFFSETS)
        runebook_index: Index of the rune in the runebook (0-15)
        material: Material name (e.g., "copper", "bronze", "verite")
    """
    data = _load_log()

    entry = {
        "timestamp": int(time.time()),
        "player_x": player_x,
        "player_y": player_y,
        "player_z": player_z or 0,
        "offset_x": offset_x,
        "offset_y": offset_y,
        "tile_x": player_x + offset_x,
        "tile_y": player_y + offset_y,
        "runebook_index": runebook_index,
        "material": material.lower(),
    }

    data["mining"].append(entry)
    _save_log(data)


def get_best_mining_spots(
    material: Optional[str] = None,
    radius: int = 5,
    top_n: int = 10,
) -> List[Dict]:
    """Get the best mining spots for a specific material or all materials.

    Args:
        material: Material name to filter by (e.g., "verite"). None = all materials.
        radius: Tiles to consider as the same spot (group nearby tiles).
        top_n: Maximum number of spots to return per material.

    Returns:
        List of dicts, each containing:
        {
            "material": "verite",
            "tile_x": 1235,
            "tile_y": 5679,
            "runebook_index": 5,
            "count": 12,
            "cluster_tiles": [(1235, 5679), (1236, 5680), ...]
        }
    """
    data = _load_log()
    entries = data.get("mining", [])

    if material:
        material = material.lower()
        entries = [e for e in entries if e.get("material") == material]

    if not entries:
        return []

    results = []

    for m in sorted(set(e["material"] for e in entries)):
        if material and m != material:
            continue

        mat_entries = [e for e in entries if e["material"] == m]

        if not mat_entries:
            continue

        tile_counts = Counter((e["tile_x"], e["tile_y"]) for e in mat_entries)

        grouped_spots = []
        processed = set()

        for (tx, ty), count in tile_counts.most_common():
            if (tx, ty) in processed:
                continue

            cluster_tiles = [(tx, ty)]
            cluster_count = count
            processed.add((tx, ty))

            for (cx, cy), ccount in tile_counts.items():
                if (cx, cy) in processed:
                    continue

                if any(
                    abs(cx - gx) <= radius and abs(cy - gy) <= radius
                    for (gx, gy) in cluster_tiles
                ):
                    cluster_tiles.append((cx, cy))
                    cluster_count += ccount
                    processed.add((cx, cy))

            grouped_spots.append(
                {
                    "material": m,
                    "tile_x": tx,
                    "tile_y": ty,
                    "count": cluster_count,
                    "cluster_tiles": cluster_tiles,
                }
            )

        grouped_spots.sort(key=lambda x: x["count"], reverse=True)
        results.extend(grouped_spots[:top_n])

    return results


def get_mining_statistics(material: Optional[str] = None) -> Dict:
    """Get statistics about mining gathers.

    Args:
        material: Material name to filter by. None = all materials.

    Returns:
        Dict with keys:
        {
            "total_gathers": 100,
            "by_material": {"verite": 42, "valorite": 15, ...},
            "by_runebook_index": {0: 10, 1: 25, ...},
            "unique_tiles": 30
        }
    """
    data = _load_log()
    entries = data.get("mining", [])

    if material:
        material = material.lower()
        entries = [e for e in entries if e.get("material") == material]

    if not entries:
        return {
            "total_gathers": 0,
            "by_material": {},
            "by_runebook_index": {},
            "unique_tiles": 0,
        }

    by_material = Counter(e["material"] for e in entries)
    by_runebook_index = Counter(e["runebook_index"] for e in entries)
    unique_tiles = len(set((e["tile_x"], e["tile_y"]) for e in entries))

    return {
        "total_gathers": len(entries),
        "by_material": dict(by_material),
        "by_runebook_index": dict(by_runebook_index),
        "unique_tiles": unique_tiles,
    }
