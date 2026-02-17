import re

from _lib.crafting import CRAFTING_DB, BODCrafter

import API
from _lib.utils import Hue, p


class BOD:
    """Represents a Bulk Order Deed with parsed crafting requirements."""

    PROFESSION_HUES = {
        1102: "Blacksmith",
        1155: "Tailor",
    }

    def __init__(self, item):
        self.item = item
        self.serial = item.Serial
        self.profession = self.PROFESSION_HUES.get(item.Hue, "Unknown")
        self.exceptional = False
        self.material = "Iron"
        self.quantity = 0
        self.item_name = None
        self.completed = 0
        self._parse()

    def _parse(self):
        """Parse BOD tooltip into structured attributes."""
        props = API.ItemNameAndProps(self.serial, True)
        if not props:
            return

        lines = [line.strip() for line in props.split("\n") if line.strip()]
        self._parse_lines(lines)

    def _parse_lines(self, lines):
        """Parse tooltip lines based on BOD variant."""
        line_count = len(lines)

        if line_count < 6:
            return

        # Look for material requirement line
        material_line = None
        exceptional_line = None
        amount_line = None
        item_line = None

        for line in lines:
            lower = line.lower()
            if "must be made with" in lower and "ingots" in lower:
                material_line = line
            elif "must be exceptional" in lower:
                exceptional_line = line
            elif line.startswith("Amount To Make:"):
                amount_line = line
            elif (
                ":" in line
                and not line.startswith("Amount")
                and not line.startswith("Weight")
            ):
                # Item line has format "Item Name: count"
                parts = line.split(":")
                if len(parts) == 2:
                    try:
                        int(parts[1].strip())
                        item_line = line
                    except ValueError:
                        pass

        # Set exceptional flag
        self.exceptional = exceptional_line is not None

        # Extract material
        if material_line:
            match = re.search(r"made with (.+?) ingots", material_line, re.I)
            if match:
                self.material = match.group(1).strip().title()

        # Extract quantity and completed count
        if item_line:
            parts = item_line.split(":")
            self.item_name = parts[0].strip()
            try:
                self.completed = int(parts[1].strip())
            except ValueError:
                self.completed = 0

        if amount_line:
            try:
                self.quantity = int(amount_line.split(":")[1].strip())
            except (IndexError, ValueError):
                self.quantity = 0

    def remaining(self):
        """Return number of items still needed."""
        return max(0, self.quantity - self.completed)

    def is_complete(self):
        """Return True if BOD is finished."""
        return self.remaining() == 0

    def get_craft_info(self):
        """Return crafting info from database if available."""
        if not self.item_name or not self.profession:
            return None
        prof_db = CRAFTING_DB.get(self.profession, {})
        return prof_db.get(self.item_name)

    def can_craft(self):
        """Return True if this BOD can be auto-crafted."""
        if not self.item_name or not self.profession:
            return False
        prof_db = CRAFTING_DB.get(self.profession, {})
        return self.item_name in prof_db and not self.is_complete()

    def __str__(self):
        status = (
            "Complete" if self.is_complete() else f"{self.completed}/{self.quantity}"
        )
        quality = "Exceptional" if self.exceptional else "Normal"
        return (
            f"[{self.profession}] {quality} {self.material} {self.item_name} ({status})"
        )

    def __repr__(self):
        return f"BOD(serial={self.serial}, item={self.item_name}, remaining={self.remaining()})"


def find_bods_in_backpack():
    """Find and parse all BODs in player backpack."""
    bods = []
    bod_graphics = [0x2258, 0x2259]  # Small and Large BODs

    for graphic in bod_graphics:
        for bod_item in API.FindTypeAll(graphic, API.Backpack) or []:
            bod = BOD(bod_item)
            if bod.item_name:  # Only add if parsing succeeded
                bods.append(bod)

    return bods


def display_bods(bods):
    """Display all BODs and their crafting status."""
    if not bods:
        p("No BODs found in backpack.", Hue.Orange)
        return

    craftable = [b for b in bods if b.can_craft()]
    not_craftable = [b for b in bods if not b.can_craft() and not b.is_complete()]
    complete = [b for b in bods if b.is_complete()]

    p(f"Found {len(bods)} BOD(s):", Hue.Green)
    p(f"  - {len(craftable)} craftable", Hue.Cyan)
    p(f"  - {len(not_craftable)} missing craft data", Hue.Yellow)
    p(f"  - {len(complete)} complete", Hue.Green)
    p("")

    for bod in bods:
        status_color = Hue.Green if bod.is_complete() else Hue.White
        if bod.can_craft():
            status_color = Hue.Cyan
        elif not bod.is_complete():
            status_color = Hue.Yellow

        p(f"  {bod}", status_color)


def craft_bods(bods):
    """Process and craft all eligible BODs."""
    craftable = [b for b in bods if b.can_craft()]

    if not craftable:
        p("No craftable BODs found!", Hue.Orange)
        p("Make sure you have craft data for the items you want to craft.", Hue.White)
        return

    p(f"\nStarting crafting for {len(craftable)} BOD(s)...", Hue.Green)

    crafter = BODCrafter()
    crafter.process_bods(craftable)


def main():
    """Main entry point."""
    bods = find_bods_in_backpack()

    if not bods:
        p("No BODs found in backpack.", Hue.Orange)
        return

    # Display mode by default
    display_bods(bods)

    # Check if any are craftable
    craftable = [b for b in bods if b.can_craft()]
    if craftable:
        p(f"\n{len(craftable)} BOD(s) can be auto-crafted.", Hue.Cyan)
        craft_bods(bods)


# Run main if executed directly
main()
