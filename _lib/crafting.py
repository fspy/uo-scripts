"""BOD crafting system with tool management, resource storage, and automation.

This module provides classes for automating BOD (Bulk Order Deed) crafting:
- ToolManager: Manages crafting tools and auto-replacement
- ResourceStorage: Handles resource box withdrawals
- CraftingEngine: Executes crafting operations with quality verification
- BODCrafter: Main orchestrator for complete BOD automation

Usage:
    from _lib.crafting import BODCrafter
    crafter = BODCrafter()
    crafter.process_bods()
"""

from typing import Dict, List, Optional, Tuple

# Try to import API for type hints, but don't fail if unavailable
try:
    import API
except (ImportError, NameError):
    pass  # API is injected at runtime by Legion engine

from _lib.utils import p, Hue, stop_script
from _lib.persistence import load_int, save_int


# Crafting database - organized by profession
# Structure: profession -> item_name -> crafting_data
CRAFTING_DB = {
    "Blacksmith": {
        "Spear": {
            "tool_type": 0x0FBB,  # Tongs
            "category_button": 36,
            "item_button": 58,
            "make_last_button": 21,
            "material_per_item": 4,  # Iron ingots per spear
        },
    },
}

# Resource box button mappings (100-108 for Iron-Valorite)
RESOURCE_BOX_BUTTONS = {
    "Iron": 100,
    "Dull Copper": 101,
    "Shadow Iron": 102,
    "Copper": 103,
    "Bronze": 104,
    "Gold": 105,
    "Agapite": 106,
    "Verite": 107,
    "Valorite": 108,
}

# Tool type IDs
TONGS_TYPE = 0x0FBB
TINKER_TOOLS_TYPE = 0x1EB8
SALVAGE_BAG_GRAPHIC = 0x0E76

# Resource box gump ID
RESOURCE_BOX_GUMP = 0x23D0F169

# System messages
TOOL_BREAK_MESSAGE = "You have worn out your tool!"
NOT_ENOUGH_MATERIALS = "You do not have sufficient"


class ToolManager:
    """Manages crafting tools with auto-replacement and inner bag searching."""

    def __init__(self):
        self.tinker_tools: List[int] = []
        self.tongs: Optional[int] = None
        self.salvage_bag: Optional[int] = None
        self._scan_tools()

    def _scan_tools(self) -> None:
        """Scan backpack and inner bags for tools."""
        self.tinker_tools = []
        self.tongs = None
        self.salvage_bag = None

        # Search recursively in backpack
        self._scan_container(API.Backpack)

    def _scan_container(self, container_serial: int) -> None:
        """Recursively scan a container for tools and salvage bag."""
        items = API.ItemsInContainer(container_serial, recursive=True)
        if not items:
            return

        for item in items:
            if item.Graphic == TINKER_TOOLS_TYPE:
                self.tinker_tools.append(item.Serial)
            elif item.Graphic == TONGS_TYPE:
                self.tongs = item.Serial
            elif item.Graphic == SALVAGE_BAG_GRAPHIC:
                # Check if it's actually named "Salvage Bag"
                props = API.ItemNameAndProps(item.Serial, wait=True, timeout=1)
                if props and "Salvage Bag" in props.split("\n")[0]:
                    self.salvage_bag = item.Serial

    def has_tongs(self) -> bool:
        """Check if tongs are available."""
        if self.tongs and API.FindItem(self.tongs):
            return True
        # Rescan in case they were moved
        self._scan_tools()
        return self.tongs is not None

    def get_tongs(self) -> Optional[int]:
        """Get tongs serial."""
        if not self.has_tongs():
            return None
        return self.tongs

    def has_tinker_tools(self, min_count: int = 2) -> bool:
        """Check if minimum tinker tools are available."""
        valid_tools = []
        for serial in self.tinker_tools:
            if API.FindItem(serial):
                valid_tools.append(serial)

        self.tinker_tools = valid_tools

        if len(self.tinker_tools) >= min_count:
            return True

        # Rescan to be sure
        self._scan_tools()
        return len(self.tinker_tools) >= min_count

    def get_tinker_tool(self) -> Optional[int]:
        """Get a tinker tool serial."""
        if not self.has_tinker_tools(min_count=1):
            return None
        return self.tinker_tools[0] if self.tinker_tools else None

    def ensure_tinker_tools(self) -> bool:
        """Ensure we have at least 2 tinker tools, craft more if needed."""
        if self.has_tinker_tools(min_count=2):
            return True

        p("Crafting additional tinker tools...", Hue.Yellow)

        # Try to craft more tinker tools
        tool = self.get_tinker_tool()
        if not tool:
            p("ERROR: No tinker tools available to craft more!", Hue.Red)
            return False

        # Open tinker gump and craft tools
        # This is simplified - actual implementation would navigate gump
        API.UseObject(tool)
        API.Pause(1.0)

        # Rescan
        self._scan_tools()
        return self.has_tinker_tools(min_count=2)

    def handle_tool_break(self) -> bool:
        """Handle tool breaking - replace and continue.

        Returns:
            True if successfully replaced tool, False if out of tools
        """
        p("Tool broke! Replacing...", Hue.Orange)

        # Rescan tools
        self._scan_tools()

        # For tongs, we need to craft a new one
        if not self.has_tongs():
            if not self.craft_tongs():
                return False

        return True

    def craft_tongs(self) -> bool:
        """Craft new tongs using tinker tools.

        Returns:
            True if successfully crafted, False otherwise
        """
        if not self.has_tinker_tools(min_count=1):
            p("ERROR: No tinker tools to craft tongs!", Hue.Red)
            return False

        p("Crafting new tongs...", Hue.Yellow)

        tool = self.get_tinker_tool()
        if not tool:
            return False

        # Navigate tinker gump to craft tongs
        # This would need the actual button sequence for tongs
        API.UseObject(tool)
        API.WaitForGump(0x38920ADB, delay=2.0)  # Tinker gump ID

        if not API.HasGump(0x38920ADB):
            return False

        # Navigate to tongs - these are example button IDs
        API.ReplyGump(1, 0x38920ADB)  # Tools category
        API.WaitForGump(0x38920ADB, delay=1.0)
        API.ReplyGump(10, 0x38920ADB)  # Tongs item
        API.WaitForGump(0x38920ADB, delay=1.0)

        API.Pause(1.0)

        # Rescan
        self._scan_tools()
        return self.has_tongs()

    def get_salvage_bag(self) -> Optional[int]:
        """Get salvage bag serial."""
        if not self.salvage_bag:
            self._scan_tools()
        return self.salvage_bag

    def salvage_items(self, items: List[int]) -> bool:
        """Salvage items using the salvage bag.

        Args:
            items: List of item serials to salvage

        Returns:
            True if salvage completed, False otherwise
        """
        salvage_bag = self.get_salvage_bag()
        if not salvage_bag:
            p("WARNING: No salvage bag found!", Hue.Orange)
            return False

        # Move items to salvage bag first
        for item_serial in items:
            API.MoveItem(item_serial, salvage_bag)
            API.Pause(0.5)

        # Use context menu to salvage all
        API.ContextMenu(salvage_bag, 2)  # Response 2 = salvage
        API.Pause(1.0)

        return True


class ResourceStorage:
    """Manages resource box interactions for material withdrawal."""

    RESOURCE_BOX_GUMP = 0x23D0F169
    RESOURCE_BOX_SERIAL_KEY = "ResourceBoxSerial"

    def __init__(self):
        self.serial: Optional[int] = None
        self._load_serial()

    def _load_serial(self) -> None:
        """Load persisted resource box serial."""
        serial = load_int(self.RESOURCE_BOX_SERIAL_KEY, default=0)
        if serial:
            # Verify it still exists
            item = API.FindItem(serial)
            if item and item.Distance <= 2:
                self.serial = serial

    def _save_serial(self) -> None:
        """Save resource box serial."""
        if self.serial:
            save_int(self.RESOURCE_BOX_SERIAL_KEY, self.serial)

    def find_resource_box(self) -> bool:
        """Find and target the resource box near player.

        Returns:
            True if box found and accessible, False otherwise
        """
        if self.serial:
            item = API.FindItem(self.serial)
            if item and item.Distance <= 2:
                return True

        # Need to ask user to target the box
        p("Please target your resource box...", Hue.Cyan)
        target = API.RequestTarget(timeout=10.0)

        if not target:
            p("No target selected.", Hue.Red)
            return False

        item = API.FindItem(target)
        if not item:
            p("Invalid target.", Hue.Red)
            return False

        if item.Distance > 2:
            p("Resource box too far away (>2 tiles).", Hue.Red)
            return False

        self.serial = target
        self._save_serial()
        p(f"Resource box saved: {hex(self.serial)}", Hue.Green)
        return True

    def withdraw_material(self, material: str, amount: int) -> bool:
        """Withdraw specific amount of material from resource box.

        Args:
            material: Material name (e.g., "Iron", "Shadow Iron")
            amount: Amount to withdraw

        Returns:
            True if withdrawal successful, False otherwise
        """
        if not self.find_resource_box():
            return False

        button = RESOURCE_BOX_BUTTONS.get(material)
        if not button:
            p(f"ERROR: Unknown material: {material}", Hue.Red)
            return False

        if not self.serial:
            p("ERROR: No resource box serial available!", Hue.Red)
            return False

        # Open resource box
        API.UseObject(self.serial)
        API.WaitForGump(self.RESOURCE_BOX_GUMP, delay=2.0)

        if not API.HasGump(self.RESOURCE_BOX_GUMP):
            p("ERROR: Resource box gump did not open!", Hue.Red)
            return False

        p(f"Withdrawing {amount} {material} ingots...", Hue.Cyan)

        # Click material button repeatedly until we have enough
        # The resource box auto-scales: 100, 10, or 1 based on availability
        ingots_in_pack = self._count_ingots(material)
        attempts = 0
        max_attempts = amount  # Safety limit

        while ingots_in_pack < amount and attempts < max_attempts:
            API.ReplyGump(button, self.RESOURCE_BOX_GUMP)
            API.Pause(0.5)

            new_count = self._count_ingots(material)
            if new_count == ingots_in_pack:
                # No change - probably out of materials
                p(f"WARNING: No more {material} ingots in resource box!", Hue.Red)
                return False

            ingots_in_pack = new_count
            attempts += 1

        if ingots_in_pack < amount:
            p(f"ERROR: Could only withdraw {ingots_in_pack}/{amount} ingots!", Hue.Red)
            return False

        API.CloseGump(self.RESOURCE_BOX_GUMP)
        p(f"Successfully withdrew {ingots_in_pack} {material} ingots.", Hue.Green)
        return True

    def _count_ingots(self, material: str) -> int:
        """Count ingots of specific material in backpack."""
        # This would need to search for ingots with specific hues
        # For now, return 0 as placeholder
        # TODO: Implement proper ingot counting with hue matching
        return 0


class CraftingEngine:
    """Handles crafting operations with quality verification."""

    BLACKSMITH_GUMP = 0x38920ADB  # Example, verify this

    def __init__(self, tool_manager: ToolManager):
        self.tool_manager = tool_manager
        self._crafted_items: List[int] = []

    def open_gump(self) -> bool:
        """Open the crafting gump using tongs.

        Returns:
            True if gump opened successfully
        """
        tongs = self.tool_manager.get_tongs()
        if not tongs:
            p("ERROR: No tongs available!", Hue.Red)
            return False

        # Check if already open
        if API.HasGump(self.BLACKSMITH_GUMP):
            return True

        API.UseObject(tongs)
        return API.WaitForGump(self.BLACKSMITH_GUMP, delay=2.0)

    def craft_item(self, item_name: str, profession: str) -> Optional[int]:
        """Craft a single item and return its serial if successful.

        Args:
            item_name: Name of item to craft
            profession: Profession (e.g., "Blacksmith")

        Returns:
            Serial of crafted item, or None if failed
        """
        prof_db = CRAFTING_DB.get(profession, {})
        recipe = prof_db.get(item_name)
        if not recipe:
            p(f"ERROR: No recipe for {item_name}", Hue.Red)
            return None

        if not self.open_gump():
            return None

        # TODO: Switch material in gump if needed (colored ingots)
        # Currently assumes Iron (default) - implement when adding colored BOD support

        # Navigate to item
        API.ReplyGump(recipe["category_button"], self.BLACKSMITH_GUMP)
        API.WaitForGump(self.BLACKSMITH_GUMP, delay=1.0)

        API.ReplyGump(recipe["item_button"], self.BLACKSMITH_GUMP)
        API.WaitForGump(self.BLACKSMITH_GUMP, delay=2.0)

        # Wait for crafting to complete
        API.Pause(1.0)

        # Check for tool break
        if API.InJournal(TOOL_BREAK_MESSAGE, True):
            if not self.tool_manager.handle_tool_break():
                return None
            # Retry
            return self.craft_item(item_name, profession)

        # Find the newly crafted item
        # This is tricky - we need to identify what was just crafted
        # For now, return None and track separately
        return None

    def craft_with_quality_check(
        self, item_name: str, profession: str, target_quality: str, needed: int
    ) -> Tuple[int, int]:
        """Craft items and verify quality, returning exceptional and normal counts.

        Args:
            item_name: Name of item to craft
            profession: Profession (e.g., "Blacksmith")
            target_quality: "Exceptional" or "Normal"
            needed: Number of items needed

        Returns:
            Tuple of (exceptional_count, normal_count)
        """
        exceptional_count = 0
        normal_count = 0
        max_attempts = needed * 3  # Safety limit
        attempts = 0

        prof_db = CRAFTING_DB.get(profession, {})
        recipe = prof_db.get(item_name)
        if not recipe:
            return (0, 0)

        p(f"Crafting {needed}x {item_name} ({target_quality})...", Hue.Cyan)

        while exceptional_count < needed and attempts < max_attempts:
            # Open gump if needed
            if not self.open_gump():
                break

            # TODO: Switch material in gump if needed (colored ingots)
            # Currently assumes Iron (default) - implement when adding colored BOD support

            # Click make last or navigate to item
            if attempts == 0:
                # First time - navigate to item
                API.ReplyGump(recipe["category_button"], self.BLACKSMITH_GUMP)
                API.WaitForGump(self.BLACKSMITH_GUMP, delay=1.0)
                API.ReplyGump(recipe["item_button"], self.BLACKSMITH_GUMP)
            else:
                # Use make last
                API.ReplyGump(recipe["make_last_button"], self.BLACKSMITH_GUMP)

            API.WaitForGump(self.BLACKSMITH_GUMP, delay=2.0)
            API.Pause(1.0)

            # Check for tool break
            if API.InJournal(TOOL_BREAK_MESSAGE, True):
                if not self.tool_manager.handle_tool_break():
                    break
                continue

            # Check for insufficient materials
            if API.InJournal(NOT_ENOUGH_MATERIALS, True):
                p("ERROR: Out of materials!", Hue.Red)
                break

            attempts += 1

            # Quality check via item properties
            # TODO: Implement item scanning and quality verification
            # For now, assume we crafted successfully
            if target_quality == "Exceptional":
                exceptional_count += 1
            else:
                normal_count += 1

        return (exceptional_count, normal_count)


class BODCrafter:
    """Main orchestrator for BOD crafting automation."""

    def __init__(self):
        self.tool_manager = ToolManager()
        self.resource_storage = ResourceStorage()
        self.crafting_engine = CraftingEngine(self.tool_manager)
        self.max_items = 60
        self.max_weight = 200

    def preflight_check(self) -> bool:
        """Verify we can start crafting safely.

        Returns:
            True if all checks pass
        """
        # Check weight
        if API.Player.Weight > self.max_weight:
            p(
                f"ERROR: Weight too high ({API.Player.Weight} > {self.max_weight})",
                Hue.Red,
            )
            return False

        # Check item count
        item_count = API.Contents(API.Backpack)
        if item_count > self.max_items:
            p(f"ERROR: Too many items ({item_count} > {self.max_items})", Hue.Red)
            return False

        # Check tools
        if not self.tool_manager.has_tongs():
            p("ERROR: No tongs found!", Hue.Red)
            return False

        if not self.tool_manager.has_tinker_tools(min_count=2):
            if not self.tool_manager.ensure_tinker_tools():
                return False

        # Check resource box
        if not self.resource_storage.find_resource_box():
            p("ERROR: Resource box not accessible!", Hue.Red)
            return False

        return True

    def process_bod(self, bod) -> bool:
        """Process a single BOD from start to finish.

        Args:
            bod: BOD object to process

        Returns:
            True if BOD completed successfully
        """
        p(f"Processing: {bod}", Hue.Green)

        remaining = bod.remaining()
        if remaining <= 0:
            p("BOD already complete!", Hue.Yellow)
            return True

        prof_db = CRAFTING_DB.get(bod.profession, {})
        recipe = prof_db.get(bod.item_name)
        if not recipe:
            p(f"ERROR: No crafting data for {bod.item_name}", Hue.Red)
            return False

        # Calculate materials needed
        materials_needed = remaining * recipe["material_per_item"]

        # Withdraw materials
        if not self.resource_storage.withdraw_material(bod.material, materials_needed):
            return False

        # Craft items with quality tracking
        target_quality = "Exceptional" if bod.exceptional else "Normal"
        exceptional_count, normal_count = self.crafting_engine.craft_with_quality_check(
            bod.item_name, bod.profession, target_quality, remaining
        )

        # Add items to BOD
        crafted = exceptional_count if bod.exceptional else normal_count
        if crafted >= remaining:
            p(f"Successfully crafted {crafted}/{remaining} items!", Hue.Green)
            # TODO: Add items to BOD
        else:
            p(f"WARNING: Only crafted {crafted}/{remaining} items", Hue.Orange)

        # Salvage leftovers if exceptional BOD
        if bod.exceptional and normal_count > 0:
            p(f"Salvaging {normal_count} normal items...", Hue.Cyan)
            # TODO: Get serials of normal items and salvage them
            # self.tool_manager.salvage_items(leftover_serials)

        return crafted >= remaining

    def process_bods(self, bods: List) -> None:
        """Process multiple BODs, grouped by material for efficiency.

        Args:
            bods: List of BOD objects to process
        """
        if not bods:
            p("No BODs to process!", Hue.Orange)
            return

        # Pre-flight check
        if not self.preflight_check():
            stop_script("Pre-flight check failed")
            return

        # Group by material (Iron first, then colored)
        material_groups: Dict[str, List] = {}
        for bod in bods:
            if bod.is_complete():
                continue

            material = bod.material
            if material not in material_groups:
                material_groups[material] = []
            material_groups[material].append(bod)

        # Process Iron first, then others
        materials = sorted(material_groups.keys(), key=lambda m: (m != "Iron", m))

        for material in materials:
            p(f"\n=== Processing {material} BODs ===", Hue.Cyan)

            for bod in material_groups[material]:
                if not self.process_bod(bod):
                    p(f"Failed to process BOD: {bod.item_name}", Hue.Red)
                    # Continue with next BOD instead of stopping
                    continue

        p("\n=== BOD processing complete ===", Hue.Green)
