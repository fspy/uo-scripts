import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from _lib.resource_tracker import get_best_mining_spots, get_mining_statistics


def print_statistics():
    """Print overall mining statistics."""
    stats = get_mining_statistics()

    print("\n=== Mining Statistics ===")
    print(f"Total gathers: {stats['total_gathers']}")
    print(f"Unique tiles: {stats['unique_tiles']}")

    if stats["by_material"]:
        print("\nBy Material:")
        for material, count in sorted(stats["by_material"].items()):
            print(f"  {material}: {count}")

    if stats["by_runebook_index"]:
        print("\nBy Runebook Index:")
        for idx, count in sorted(stats["by_runebook_index"].items()):
            print(f"  Rune #{idx}: {count}")


def print_best_spots(material=None, radius=5, top_n=10):
    """Print best mining spots."""
    spots = get_best_mining_spots(material=material, radius=radius, top_n=top_n)

    if not spots:
        print("\nNo mining data found.")
        return

    title = "Best Mining Spots"
    if material:
        title += f" for {material.capitalize()}"
    print(f"\n=== {title} ===")

    current_material = None
    for i, spot in enumerate(spots, 1):
        if spot["material"] != current_material:
            current_material = spot["material"]
            print(f"\n{current_material.capitalize()}:")

        cluster_info = ""
        if len(spot["cluster_tiles"]) > 1:
            cluster_info = f" ({len(spot['cluster_tiles'])} tiles in cluster)"

        print(
            f"  {i}. Rune #{spot['runebook_index']}, Tile "
            f"({spot['tile_x']}, {spot['tile_y']}) - {spot['count']} gathers{cluster_info}"
        )


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Query mining resource data")
    parser.add_argument(
        "--stats", action="store_true", help="Show overall mining statistics"
    )
    parser.add_argument(
        "--material", type=str, help="Filter by material (e.g., verite, copper, bronze)"
    )
    parser.add_argument(
        "--radius",
        type=int,
        default=5,
        help="Tiles to consider as same spot (default: 5)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Maximum spots to show per material (default: 10)",
    )

    args = parser.parse_args()

    if args.stats:
        print_statistics()
    else:
        print_best_spots(material=args.material, radius=args.radius, top_n=args.top)


if __name__ == "__main__":
    main()
