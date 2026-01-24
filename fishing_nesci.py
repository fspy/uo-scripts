# =========== Consolidated Imports ============#
from base64 import b64encode
from collections import OrderedDict
from decimal import Decimal
import API
import System
import datetime
import importlib
import json
import os
import re
import sys
import time
import traceback
import urllib.request


# =========== Start of LegionPath.py ============#


class LegionPath:
    @staticmethod
    def createPath(path):
        path = f"{LegionPath.getLegionPath()}/{path}"
        return path

    @staticmethod
    def getLegionPath():
        base = sys.prefix
        if base.lower().endswith("ironpython.dll"):
            base = os.path.dirname(base)

        legion_path = os.path.join(base, "LegionScripts")
        return legion_path

    @staticmethod
    def addSubdirs():
        legion_path = LegionPath.getLegionPath()

        if not os.path.isdir(legion_path):
            return

        for name in os.listdir(legion_path):
            subdir = os.path.join(legion_path, name)
            if os.path.isdir(subdir) and name.startswith("_"):
                if subdir not in sys.path:
                    sys.path.append(subdir)


# =========== End of LegionPath.py ============#

# =========== Start of _Utils\Error.py ============#


class Error:
    @staticmethod
    def error(msg, isStopping=True):
        API.SysMsg(msg, 33)
        if isStopping:
            API.Stop()

    @staticmethod
    def logError(e, scriptName):
        error_message = f"{scriptName} e: {e}"
        tb = traceback.format_exc()
        API.SysMsg(error_message, 33)
        API.SysMsg(tb)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logFile = f"{timestamp}_{scriptName}_crash.log"
        with open(logFile, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] {error_message}\n")
            f.write(f"{tb}\n\n")


# =========== End of _Utils\Error.py ============#

# =========== Start of _Utils\Math.py ============#


class Math:
    centerX = 1323
    mapWidth = 5120
    centerY = 1624
    mapHeight = 4096

    @staticmethod
    def truncateDecimal(n1, d=1):
        n = str(n1)
        return n if "." not in n else n[: n.find(".") + d + 1]

    @staticmethod
    def distanceBetween(m1, m2):
        if not m1 or not m2:
            return 999
        return max(abs(m1.X - m2.X), abs(m1.Y - m2.Y))

    @staticmethod
    def convertToHex(obj):
        if isinstance(obj, dict):
            return {k: Math.convertToHex(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [Math.convertToHex(elem) for elem in obj]
        elif isinstance(obj, str) and re.fullmatch(r"0x[0-9a-fA-F]+", obj):
            return int(obj, 16)
        return obj

    @staticmethod
    def tilesToLatLon(x, y):
        degLon = (x - Math.centerX) * 360.0 / Math.mapWidth
        degLat = (y - Math.centerY) * 360.0 / Math.mapHeight

        if degLon > 180:
            degLon = 360 - degLon
            lonDir = "W"
        else:
            lonDir = "E"

        if degLat > 180:
            degLat = 360 - degLat
            latDir = "N"
        else:
            latDir = "S"

        lat = (int(degLat), (degLat - int(degLat)) * 60, latDir)
        lon = (int(degLon), (degLon - int(degLon)) * 60, lonDir)
        return lat, lon

    @staticmethod
    def latLonToTiles(degLat, minLat, latDir, degLon, minLon, lonDir):
        totalLat = degLat + minLat / 60
        if latDir == "N":
            totalLat = 360 - totalLat

        totalLon = degLon + minLon / 60
        if lonDir == "W":
            totalLon = 360 - totalLon

        y = totalLat * Math.mapHeight / 360 + Math.centerY
        x = totalLon * Math.mapWidth / 360 + Math.centerX
        return int(x % Math.mapWidth), int(y % Math.mapHeight)


# =========== End of _Utils\Math.py ============#

# =========== Start of _Utils\Util.py ============#


class Util:
    skillNames = [
        "Archery",
        "Chivalry",
        "Fencing",
        "Focus",
        "Mace Fighting",
        "Parrying",
        "Swordsmanship",
        "Tactics",
        "Wrestling",
        "Bushido",
        "Throwing",
        "Healing",
        "Veterinary",
        "Alchemy",
        "Evaluating Intelligence",
        "Inscription",
        "Magery",
        "Meditation",
        "Necromancy",
        "Resisting Spells",
        "Spellweaving",
        "Spirit Speak",
        "Mysticism",
        "Discordance",
        "Musicianship",
        "Peacemaking",
        "Provocation",
        "Begging",
        "Detecting Hidden",
        "Hiding",
        "Lockpicking",
        "Poisoning",
        "Remove Trap",
        "Snooping",
        "Stealing",
        "Stealth",
        "Ninjitsu",
        "Anatomy",
        "Animal Lore",
        "Animal Taming",
        "Camping",
        "Forensic Evaluation",
        "Herding",
        "Taste Identification",
        "Tracking",
        "Arms Lore",
        "Blacksmithy",
        "Bowcraft/Fletching",
        "Carpentry",
        "Cooking",
        "Item Identification",
        "Cartography",
        "Tailoring",
        "Tinkering",
        "Imbuing",
        "Fishing",
        "Mining",
        "Lumberjacking",
    ]

    layers = [
        "OneHanded",
        "TwoHanded",
        "Shoes",
        "Pants",
        "Shirt",
        "Helmet",
        "Gloves",
        "Ring",
        "Talisman",
        "Necklace",
        "Hair",
        "Waist",
        "Torso",
        "Bracelet",
        "Face",
        "Beard",
        "Tunic",
        "Earrings",
        "Arms",
        "Cloak",
        "Robe",
        "Skirt",
        "Legs",
    ]

    @staticmethod
    def getWeaponName():
        twoHandedWeapon = API.FindLayer("TwoHanded")
        if twoHandedWeapon:
            props = API.ItemNameAndProps(twoHandedWeapon.Serial, True).split("\n")
            return props[0].strip()
        oneHandedWeapon = API.FindLayer("OneHanded")
        if oneHandedWeapon:
            props = API.ItemNameAndProps(oneHandedWeapon.Serial, True).split("\n")
            return props[0].strip()

    @staticmethod
    def getPlayerName():
        while not API.Player.Name:
            API.Pause(0.1)
        playerName = API.Player.Name.replace("Lady ", "").replace("Lord ", "")
        return playerName

    @staticmethod
    def getMasterContainer(corpseSerial):
        corpseItem = API.FindItem(corpseSerial)
        API.SysMsg(str(corpseItem))
        if corpseItem.Container:
            corpseItem = API.FindItem(corpseItem.Container)
            API.SysMsg(f"container: {str(corpseItem)}")
            return corpseItem
        return corpseItem

    @staticmethod
    def scanEnemies(range=15):
        enemies = API.NearestMobiles(
            [
                API.Notoriety.Enemy,
                API.Notoriety.Criminal,
                API.Notoriety.Gray,
                API.Notoriety.Murderer,
            ],
            range,
        )
        enemies = [m for m in enemies if not m.IsRenamable and m.HasLineOfSightFrom()]
        enemies = sorted(enemies, key=lambda m: Math.distanceBetween(API.Player, m))
        return enemies

    @staticmethod
    def getStatValue(statName):
        rawStat = getattr(API.Player, statName)
        for layer in Util.layers:
            item = API.FindLayer(layer)
            if item:
                props = API.ItemNameAndProps(item.Serial).split("\n")
                for prop in props:
                    if f"{statName} Bonus".lower() in prop.lower():
                        bonus = prop.split("Bonus ")[1]
                        rawStat -= int(bonus)
        return rawStat

    @staticmethod
    def useObject(objectSerial):
        API.CancelTarget()
        object = API.FindItem(objectSerial)
        if not object:
            API.SysMsg(f"Object {str(objectSerial)} not found")
        API.UseObject(object.Serial)

    @staticmethod
    def useObjectWithTarget(objectSerial):
        API.CancelTarget()
        while not API.WaitForTarget("any", 3):
            Util.useObject(objectSerial)

    @staticmethod
    def closeGump(gumpId):
        while API.HasGump(gumpId):
            API.SysMsg("Closing GUMP")
            API.CloseGump(gumpId)
            API.Pause(0.5)
            API.SysMsg(f"API.HasGump(gumpId) 1: {str(API.HasGump(gumpId))}")

    @staticmethod
    def openGumpObject(objectSerial, gumpId):
        Util.closeGump(gumpId)
        while not API.HasGump(gumpId):
            Util.useObject(objectSerial)
            API.Pause(0.5)
        API.SysMsg(f"API.HasGump(gumpId) 2: {str(API.HasGump(gumpId))}")
        gump = API.GetGump(gumpId)
        return gump

    @staticmethod
    def openGumpSkill(skillName, targetSerial, gumpId):
        while not API.HasGump(gumpId):
            API.UseSkill(skillName)
            API.WaitForTarget("any", 1)
            API.Target(targetSerial)
            API.Pause(0.1)

    @staticmethod
    def getCharSkillInfo():
        totalPlus = 0
        totalMinus = 0
        for skillName in Util.skillNames:
            values = Util.getSkillInfo(skillName)
            skillValue = values["value"]
            lock = values["lock"]
            if lock == "Locked" or lock == "Up":
                totalPlus += skillValue
            else:
                totalMinus += skillValue
        return {"totalPlus": totalPlus, "totalMinus": totalMinus}

    @staticmethod
    def getSkillInfo(skillName):
        values = API.GetSkill(skillName)
        v = Decimal(Math.truncateDecimal(values.Value))
        c = Decimal(Math.truncateDecimal(values.Cap))
        l = str(values.Lock)
        return {"value": v, "cap": c, "lock": l}

    @staticmethod
    def isWearingWeapon():
        oneHanded = bool(API.FindLayer("OneHanded"))
        if oneHanded:
            return True
        twoHanded = bool(API.FindLayer("TwoHanded"))
        return twoHanded

    @staticmethod
    def getTotalSkillPoints():
        total = 0
        for skill in Util.skillNames:
            value = Util.getSkillInfo(skill)["value"]
            total += value
        return total

    @staticmethod
    def findItemWithProps(props):
        items = Util.itemsInContainer(API.Backpack)
        for item in items:
            itemProps = API.ItemNameAndProps(item.Serial).split("\n")
            if all(any(p in itemProp for itemProp in itemProps) for p in props):
                return item

    @staticmethod
    def isTargeting():
        return API.WaitForTarget("any", 0)

    @staticmethod
    def getTypeOfTarget():
        res = None
        if API.WaitForTarget("Neutral", 0):
            res = "Neutral"
        elif API.WaitForTarget("Harmful", 0):
            res = "Harmful"
        elif API.WaitForTarget("Beneficial", 0):
            res = "Beneficial"
        else:
            res = None
        return res

    @staticmethod
    def checkIfGearBroken():
        for layer in Util.layers:
            item = API.FindLayer(layer)
            if item:
                props = API.ItemNameAndProps(item.Serial).split("\n")
                for prop in props:
                    if "durability 0 /" in prop.lower():
                        return True
        return False

    @staticmethod
    def itemsInContainer(containerSerial):
        allItems = API.ItemsInContainer(containerSerial, True)
        if len(allItems) == 1 and allItems[0].Graphic == 8198:
            allItems = API.ItemsInContainer(allItems[0].Serial, True)
        return allItems

    @staticmethod
    def findTypeAll(containerId, itemId, hue=None):
        filteredItems = []
        items = Util.itemsInContainer(containerId)
        for item in items:
            if item.Graphic == itemId:
                if hue and item.Hue == hue:
                    filteredItems.append(item)
                if not hue:
                    filteredItems.append(item)
        return filteredItems

    @staticmethod
    def findCorpses(range=7):
        items = API.FindTypeAll(8198, 4294967295, range)
        return items

    @staticmethod
    def findTypeWorld(itemId, range=2):
        item = API.FindType(itemId, 4294967295, range)
        return item

    @staticmethod
    def findType(containerId, itemId):
        items = Util.itemsInContainer(containerId)
        for item in items:
            if item.Graphic == itemId:
                return item
        return None

    @staticmethod
    def findTypeWithSpecialHue(resourceId, container, minAmount, resourceHue):
        resource = API.FindType(
            resourceId, container, hue=resourceHue, minamount=minAmount
        )
        return resource

    @staticmethod
    def openContainer(container):
        if isinstance(container, System.UInt32):
            container = API.FindItem(container)
        isOpened = container.Opened
        if not isOpened:
            API.UseObject(container.Serial)
            API.Pause(1)

    @staticmethod
    def moveItemOffset(itemSerial, xOffset=0, yOffset=1, amount=0, maxRetries=5):
        for attempt in range(maxRetries):
            API.ClearJournal()
            API.MoveItemOffset(itemSerial, amount, xOffset, yOffset, OSI=True)
            API.Pause(1)

            if not API.InJournal("You must wait to perform another action."):
                return True

            API.SysMsg(f"Retrying move ({attempt + 1}/{maxRetries})...", 33)
            API.Pause(1)

        API.SysMsg("Move failed after retries.", 33)
        return False

    @staticmethod
    def moveItem(itemSerial, destinationSerial, amount=0, maxRetries=5):
        for attempt in range(maxRetries):
            API.ClearJournal()
            API.MoveItem(itemSerial, destinationSerial, amount)
            API.Pause(1)

            if not API.InJournal("You must wait to perform another action."):
                return True

            API.SysMsg(f"Retrying move ({attempt + 1}/{maxRetries})...", 33)
            API.Pause(1)

        API.SysMsg("Move failed after retries.", 33)
        return False

    @staticmethod
    def getContents(item):
        props = API.ItemNameAndProps(item.Serial, True).split("\n")
        for prop in props:
            if "Contents" in prop:
                match = re.search(
                    r"Content[s]?:\s*(\d+)/\d+\s+Items,\s*(\d+)(?:/\d+)?\s+Stones", prop
                )
                if match:
                    result = {
                        "items": int(match.group(1)),
                        "stones": int(match.group(2)),
                    }
                else:
                    result = {"items": None, "stones": None}
                return result


# =========== End of _Utils\Util.py ============#

# =========== Start of _Jsons\spell_def_magic.py ============#
SPELLS = [
    {"castTime": 1, "hasTarget": False, "manaCost": 4, "name": "Create Food"},
    {"castTime": 1, "hasTarget": False, "manaCost": 4, "name": "Reactive Armor"},
    {"castTime": 1, "hasTarget": True, "manaCost": 4, "name": "Clumsy"},
    {"castTime": 1, "hasTarget": True, "manaCost": 4, "name": "Feeblemind"},
    {"castTime": 1, "hasTarget": True, "manaCost": 4, "name": "Heal"},
    {"castTime": 1, "hasTarget": True, "manaCost": 4, "name": "Magic Arrow"},
    {"castTime": 1, "hasTarget": False, "manaCost": 4, "name": "Night Sight"},
    {"castTime": 1, "hasTarget": True, "manaCost": 4, "name": "Weaken"},
    {"castTime": 1.25, "hasTarget": True, "manaCost": 6, "name": "Agility"},
    {"castTime": 1.25, "hasTarget": True, "manaCost": 6, "name": "Cunning"},
    {"castTime": 1.25, "hasTarget": True, "manaCost": 6, "name": "Cure"},
    {"castTime": 1.25, "hasTarget": True, "manaCost": 6, "name": "Harm"},
    {"castTime": 1.25, "hasTarget": True, "manaCost": 6, "name": "Magic Trap"},
    {"castTime": 1.25, "hasTarget": True, "manaCost": 6, "name": "Remove Trap"},
    {"castTime": 1.25, "hasTarget": False, "manaCost": 6, "name": "Protection"},
    {"castTime": 1.25, "hasTarget": True, "manaCost": 6, "name": "Strength"},
    {"castTime": 1.5, "hasTarget": True, "manaCost": 9, "name": "Bless"},
    {"castTime": 1.5, "hasTarget": True, "manaCost": 9, "name": "Fireball"},
    {"castTime": 1.5, "hasTarget": True, "manaCost": 9, "name": "Magic Lock"},
    {"castTime": 1.5, "hasTarget": True, "manaCost": 9, "name": "Poison"},
    {"castTime": 1.5, "hasTarget": True, "manaCost": 9, "name": "Telekinesis"},
    {"castTime": 1.5, "hasTarget": True, "manaCost": 9, "name": "Teleport"},
    {"castTime": 1.5, "hasTarget": True, "manaCost": 9, "name": "Unlock"},
    {"castTime": 1.75, "hasTarget": True, "manaCost": 11, "name": "Wall of Stone"},
    {"castTime": 1.75, "hasTarget": False, "manaCost": 11, "name": "Arch Cure"},
    {"castTime": 1.75, "hasTarget": False, "manaCost": 11, "name": "Arch Protection"},
    {"castTime": 1.75, "hasTarget": True, "manaCost": 11, "name": "Curse"},
    {"castTime": 1.75, "hasTarget": False, "manaCost": 11, "name": "Fire Field"},
    {"castTime": 1.75, "hasTarget": True, "manaCost": 11, "name": "Greater Heal"},
    {"castTime": 1.75, "hasTarget": True, "manaCost": 11, "name": "Lightning"},
    {"castTime": 1.75, "hasTarget": True, "manaCost": 11, "name": "Mana Drain"},
    {"castTime": 1.75, "hasTarget": False, "manaCost": 11, "name": "Recall"},
    {"castTime": 5.5, "hasTarget": True, "manaCost": 14, "name": "Blade Spirits"},
    {"castTime": 1.5, "hasTarget": True, "manaCost": 14, "name": "Dispel Field"},
    {"castTime": 1.5, "hasTarget": False, "manaCost": 14, "name": "Incognito"},
    {"castTime": 1.5, "hasTarget": False, "manaCost": 14, "name": "Magic Reflection"},
    {"castTime": 1.5, "hasTarget": True, "manaCost": 14, "name": "Mind Blast"},
    {"castTime": 1.5, "hasTarget": True, "manaCost": 14, "name": "Paralyze"},
    {"castTime": 1.5, "hasTarget": False, "manaCost": 14, "name": "Poison Field"},
    {"castTime": 9, "hasTarget": False, "manaCost": 14, "name": "Summon Creature"},
    {"castTime": 1.75, "hasTarget": True, "manaCost": 20, "name": "Dispel"},
    {"castTime": 1.75, "hasTarget": True, "manaCost": 20, "name": "Energy Bolt"},
    {"castTime": 1.75, "hasTarget": True, "manaCost": 20, "name": "Explosion"},
    {"castTime": 1.75, "hasTarget": False, "manaCost": 20, "name": "Invisibility"},
    {"castTime": 1.75, "hasTarget": False, "manaCost": 20, "name": "Mark"},
    {"castTime": 1.75, "hasTarget": False, "manaCost": 20, "name": "Mass Curse"},
    {"castTime": 1.75, "hasTarget": False, "manaCost": 20, "name": "Paralyze Field"},
    {"castTime": 1.75, "hasTarget": False, "manaCost": 20, "name": "Reveal"},
    {"castTime": 2, "hasTarget": False, "manaCost": 40, "name": "Chain Lightning"},
    {"castTime": 2, "hasTarget": False, "manaCost": 40, "name": "Energy Field"},
    {"castTime": 2, "hasTarget": True, "manaCost": 40, "name": "Flamestrike"},
    {"castTime": 2, "hasTarget": False, "manaCost": 40, "name": "Gate Travel"},
    {"castTime": 2, "hasTarget": True, "manaCost": 40, "name": "Mana Vampire"},
    {"castTime": 2, "hasTarget": False, "manaCost": 40, "name": "Mass Dispel"},
    {"castTime": 2, "hasTarget": False, "manaCost": 40, "name": "Meteor Swarm"},
    {"castTime": 2, "hasTarget": False, "manaCost": 40, "name": "Polymorph"},
    {"castTime": 2, "hasTarget": False, "manaCost": 40, "name": "Earthquake"},
    {"castTime": 2.25, "hasTarget": True, "manaCost": 50, "name": "Energy Vortex"},
    {"castTime": 2.25, "hasTarget": True, "manaCost": 50, "name": "Resurrection"},
    {"castTime": 2.25, "hasTarget": False, "manaCost": 50, "name": "Air Elemental"},
    {"castTime": 2.25, "hasTarget": False, "manaCost": 50, "name": "Air Elemental"},
    {"castTime": 2.25, "hasTarget": False, "manaCost": 50, "name": "Summon Daemon"},
    {"castTime": 2.25, "hasTarget": False, "manaCost": 50, "name": "Earth Elemental"},
    {"castTime": 2.25, "hasTarget": False, "manaCost": 50, "name": "Fire Elemental"},
    {"castTime": 2.25, "hasTarget": False, "manaCost": 50, "name": "Water Elemental"},
    {"castTime": 1.5, "hasTarget": True, "manaCost": 14, "name": "Animate Dead"},
    {"castTime": 1.5, "hasTarget": True, "manaCost": 9, "name": "Blood Oath"},
    {"castTime": 1.5, "hasTarget": False, "manaCost": 11, "name": "Corpse Skin"},
    {"castTime": 0.75, "hasTarget": False, "manaCost": 7, "name": "Curse Weapon"},
    {"castTime": 0.75, "hasTarget": False, "manaCost": 7, "name": "Evil Omen"},
    {"castTime": 2, "hasTarget": False, "manaCost": 11, "name": "Horrific Beast"},
    {"castTime": 2, "hasTarget": False, "manaCost": 23, "name": "Lich Form"},
    {"castTime": 1.5, "hasTarget": True, "manaCost": 17, "name": "Mind Rot"},
    {"castTime": 1, "hasTarget": True, "manaCost": 10, "name": "Pain Spike"},
    {"castTime": 1.5, "hasTarget": True, "manaCost": 17, "name": "Poison Strike"},
    {"castTime": 2, "hasTarget": True, "manaCost": 23, "name": "Strangle"},
    {"castTime": 2, "hasTarget": True, "manaCost": 24, "name": "Summon Familiar"},
    {"castTime": 2, "hasTarget": False, "manaCost": 24, "name": "Vampiric Embrace"},
    {"castTime": 2, "hasTarget": False, "manaCost": 20, "name": "Vengeful Spirit"},
    {"castTime": 1.5, "hasTarget": False, "manaCost": 20, "name": "Wither"},
    {"castTime": 2, "hasTarget": False, "manaCost": 17, "name": "Wraith Form"},
    {"castTime": 2, "hasTarget": True, "manaCost": 17, "name": "Exorcism"},
    {"castTime": 1, "hasTarget": True, "manaCost": 10, "name": "Cleanse by Fire"},
    {"castTime": 1.5, "hasTarget": True, "manaCost": 10, "name": "Close Wounds"},
    {"castTime": 0.5, "hasTarget": False, "manaCost": 7, "name": "Consecrate Weapon"},
    {"castTime": 0.25, "hasTarget": False, "manaCost": 5, "name": "Dispel Evil"},
    {"castTime": 1, "hasTarget": False, "manaCost": 9, "name": "Divine Fury"},
    {"castTime": 0.5, "hasTarget": False, "manaCost": 11, "name": "Enemy of One"},
    {"castTime": 1.75, "hasTarget": False, "manaCost": 14, "name": "Holy Light"},
    {"castTime": 1.5, "hasTarget": False, "manaCost": 20, "name": "Noble Sacrifice"},
    {"castTime": 1.5, "hasTarget": False, "manaCost": 20, "name": "Remove Curse"},
    {"castTime": 1.5, "hasTarget": False, "manaCost": 20, "name": "Sacred Journey"},
    {"castTime": 0.5, "hasTarget": False, "manaCost": 24, "name": "Arcane Circle"},
    {"castTime": 3, "hasTarget": True, "manaCost": 20, "name": "Gift of Renewal"},
    {"castTime": 1, "hasTarget": False, "manaCost": 10, "name": "Immolating Weapon"},
    {"castTime": 1, "hasTarget": False, "manaCost": 11, "name": "Attune Weapon"},
    {"castTime": 1.5, "hasTarget": False, "manaCost": 14, "name": "Thunderstorm"},
    {"castTime": 1.5, "hasTarget": False, "manaCost": 24, "name": "Nature's Fury"},
    {"castTime": 1.5, "hasTarget": True, "manaCost": 20, "name": "Summon Fey"},
    {"castTime": 2, "hasTarget": True, "manaCost": 24, "name": "Summon Fiend"},
    {"castTime": 2.5, "hasTarget": False, "manaCost": 24, "name": "Reaper Form"},
    {"castTime": 2.5, "hasTarget": False, "manaCost": 32, "name": "Wildfire"},
    {"castTime": 3, "hasTarget": False, "manaCost": 32, "name": "Essence of Wind"},
    {"castTime": 3, "hasTarget": False, "manaCost": 32, "name": "Dryad Allure"},
    {"castTime": 3.5, "hasTarget": False, "manaCost": 40, "name": "Ethereal Voyage"},
    {"castTime": 3.5, "hasTarget": True, "manaCost": 40, "name": "Word of Death"},
    {"castTime": 4, "hasTarget": True, "manaCost": 40, "name": "Gift of Life"},
    {"castTime": 3, "hasTarget": False, "manaCost": 24, "name": "Arcane Empowerment"},
    {"castTime": 1, "hasTarget": True, "manaCost": 9, "name": "Nether Bolt"},
    {"castTime": 5.5, "hasTarget": False, "manaCost": 12, "name": "Healing Stone"},
    {"castTime": 1.5, "hasTarget": False, "manaCost": 14, "name": "Purge Magic"},
    {"castTime": 0.75, "hasTarget": False, "manaCost": 10, "name": "Enchant"},
    {"castTime": 1.75, "hasTarget": False, "manaCost": 17, "name": "Sleep"},
    {"castTime": 1.75, "hasTarget": False, "manaCost": 17, "name": "Eagle Strike"},
    {"castTime": 2, "hasTarget": False, "manaCost": 24, "name": "Animated Weapon"},
    {"castTime": 2, "hasTarget": False, "manaCost": 20, "name": "Stone Form"},
    {"castTime": 5.5, "hasTarget": False, "manaCost": 50, "name": "Spell Trigger"},
    {"castTime": 2, "hasTarget": False, "manaCost": 24, "name": "Mass Sleep"},
    {"castTime": 2, "hasTarget": False, "manaCost": 24, "name": "Cleansing Winds"},
    {"castTime": 2.75, "hasTarget": False, "manaCost": 30, "name": "Bombard"},
    {"castTime": 2.5, "hasTarget": False, "manaCost": 24, "name": "Spell Plague"},
    {"castTime": 2.5, "hasTarget": False, "manaCost": 28, "name": "Hail Storm"},
    {"castTime": 2.75, "hasTarget": True, "manaCost": 30, "name": "Nether Cyclone"},
    {"castTime": 2.75, "hasTarget": True, "manaCost": 40, "name": "Rising Colossus"},
    {"castTime": 0, "hasTarget": False, "manaCost": 4, "name": "Inspire"},
    {"castTime": 0, "hasTarget": False, "manaCost": 4, "name": "Invigorate"},
    {"castTime": 0, "hasTarget": False, "manaCost": 4, "name": "Resilience"},
    {"castTime": 0, "hasTarget": False, "manaCost": 4, "name": "Perseverance"},
    {"castTime": 0, "hasTarget": False, "manaCost": 4, "name": "Tribulation"},
    {"castTime": 0, "hasTarget": False, "manaCost": 4, "name": "Despair"},
    {"castTime": 0, "hasTarget": False, "manaCost": 6, "name": "Death Ray"},
    {"castTime": 0, "hasTarget": False, "manaCost": 6, "name": "Ethereal Burst"},
    {"castTime": 0, "hasTarget": False, "manaCost": 6, "name": "Nether Blast"},
    {"castTime": 0, "hasTarget": False, "manaCost": 4, "name": "Mystic Weapon"},
    {"castTime": 0, "hasTarget": False, "manaCost": 6, "name": "Command Undead"},
    {"castTime": 0, "hasTarget": False, "manaCost": 6, "name": "Conduit"},
    {"castTime": 0, "hasTarget": False, "manaCost": 6, "name": "Mana Shield"},
    {"castTime": 0, "hasTarget": False, "manaCost": 6, "name": "Summon Reaper"},
    {"castTime": 0, "hasTarget": False, "manaCost": 3, "name": "Honorable Execution"},
    {"castTime": 0, "hasTarget": False, "manaCost": 3, "name": "Counter Attack"},
    {"castTime": 0, "hasTarget": False, "manaCost": 3, "name": "Lightning Strike"},
    {"castTime": 0, "hasTarget": False, "manaCost": 3, "name": "Confidence"},
    {"castTime": 0, "hasTarget": False, "manaCost": 3, "name": "Evasion"},
    {"castTime": 0, "hasTarget": False, "manaCost": 3, "name": "Momentum Strike"},
    {"castTime": 1, "hasTarget": True, "manaCost": 40, "name": "Combat Training"},
]
# =========== End of _Jsons\spell_def_magic.py ============#

# =========== Start of _Utils\Magic.py ============#


class Magic:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Magic, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.recallMethod = self._getRecallMethod()
        self._lastCastTime = 0

    @staticmethod
    def _now():
        return time.time()

    @staticmethod
    def regenMana(manaRequired):
        if API.Player.Mana >= manaRequired:
            return
        lastAttempt = 0
        while API.Player.Mana < API.Player.ManaMax:
            if not API.BuffExists("Actively Meditating"):
                now = time.time()
                if now - lastAttempt >= 11:
                    API.UseSkill("Meditation")
                    lastAttempt = now
            API.Pause(0.1)

    @staticmethod
    def getFcDelay(castingTime):
        fc = getattr(API.Player, "FasterCasting", 0)
        return max(castingTime - (fc * 0.25), 0)

    @staticmethod
    def getFcrDelay():
        fcr = getattr(API.Player, "FasterCastRecovery", 0)
        return max(1.5 - (fcr * 0.25), 0)

    @staticmethod
    def getManaCost(baseCost):
        lmc = getattr(API.Player, "LowerManaCost", 0)
        return max(1, round(baseCost * (1 - lmc / 100.0)))

    def findSpellDef(self, spellName):
        for spell in SPELLS:
            if spell["name"].lower() == spellName.lower():
                return spell
        return None

    def hasSpell(self, spellName):
        API.ClearJournal()
        API.CastSpell(spellName)
        API.Pause(0.1)
        return not self._checkNoSpell()

    def cast(self, spellName, maxTries=3):
        API.SysMsg(spellName)
        spellDef = self.findSpellDef(spellName)
        if not spellDef:
            API.SysMsg(f"Invalid spell name: {spellName}", 33)
            return False

        manaNeeded = self.getManaCost(spellDef["manaCost"])

        for _ in range(maxTries):
            API.ClearJournal()
            if API.Player.Mana < manaNeeded:
                self.regenMana(manaNeeded)
            API.CastSpell(spellName)
            self._lastCastTime = self._now()
            castStart = self._now()
            retry = False
            while self._now() - castStart < spellDef["castTime"]:
                if spellDef["hasTarget"] and Util.isTargeting():
                    return True
                if self._checkNoSpell():
                    API.SysMsg(f"You do not have that spell: {spellName}", 33)
                    return False
                if self._checkFizzleJournal():
                    API.SysMsg(f"Spell fizzled: {spellName}", 33)
                    retry = True
                    break
                if self._checkManaFailureJournal():
                    API.SysMsg("Not enough mana, retrying", 33)
                    self.regenMana(manaNeeded)
                    retry = True
                    break
                if self._checkRecoveredJournal():
                    retry = True
                    break
                API.Pause(0.05)
            if spellDef["hasTarget"] and Util.isTargeting():
                return True
            if not retry:
                return True
            API.Pause(0.1)
        return True

    def healCure(self, greaterHealOffset=20, healOffset=10):
        player = API.Player
        skills = {
            s: API.GetSkill(s).Value
            for s in ["Magery", "Chivalry", "Spellweaving", "Spirit Speak"]
        }
        while API.BuffExists("Poisoned"):
            if skills["Magery"] >= 30 and self.cast("Cure"):
                pass
            elif skills["Chivalry"] >= 30 and self.cast("Remove Curse"):
                pass
            elif skills["Spellweaving"] >= 24 and self.cast("Essence of Wind"):
                pass
            else:
                break
            if API.WaitForTarget("any", 3):
                API.TargetSelf()
        while player.Hits < player.HitsMax - greaterHealOffset:
            if skills["Magery"] >= 50 and self.cast("Greater Heal"):
                API.WaitForTarget("any", 3)
                API.TargetSelf()
            elif skills["Magery"] >= 30 and self.cast("Heal"):
                API.WaitForTarget("any", 3)
                API.TargetSelf()
            elif skills["Chivalry"] >= 30 and self.cast("Close Wounds"):
                API.WaitForTarget("any", 3)
                API.TargetSelf()
            elif skills["Spirit Speak"] >= 30:
                API.UseSkill("Spirit Speak")
                API.Pause(7)
                continue
            elif (
                skills["Spellweaving"] >= 24
                and not API.BuffExists("Gift of Renewal")
                and self.cast("Gift of Renewal")
            ):
                API.WaitForTarget("any", 3)
                API.TargetSelf()
            else:
                bandage = API.FindType(0x0E21, API.Backpack)
                if bandage:
                    API.UseObject(bandage)
                    if API.WaitForTarget("any", 3):
                        API.TargetSelf()
                        API.Pause(7)
                break
        while player.Hits < player.HitsMax - healOffset:
            if skills["Magery"] >= 30 and self.cast("Heal"):
                API.WaitForTarget("any", 3)
                API.TargetSelf()
            elif skills["Chivalry"] >= 30 and self.cast("Close Wounds"):
                API.WaitForTarget("any", 3)
                API.TargetSelf()
            elif skills["Spirit Speak"] >= 30:
                API.UseSkill("Spirit Speak")
                API.Pause(7)
            else:
                break

    def recallToLocation(self, index, runebookItem):
        API.UseObject(runebookItem)
        API.Pause(1)
        if not API.HasGump(89):
            API.SysMsg("Runebook's gump did not open", 33)
            return
        API.ClearJournal()
        method = self._getRecallMethod()
        if method == "magery":
            API.ReplyGump(index + 50, 89)
        elif method == "chivalry":
            API.ReplyGump(index + 74, 89)
        else:
            API.SysMsg("No recall method available", 33)
            return
        # Retry if fizzled
        start = self._now()
        while self._now() - start < 4:
            if self._checkFizzleJournal():
                self.recallToLocation(index, runebookItem)
                break
            if not API.HasGump(89):
                break
            API.Pause(0.1)

    def _checkRecoveredJournal(self):
        return API.InJournalAny(["You have not yet recovered from casting a spell."])

    def _checkAlreadyCastingJournal(self):
        return API.InJournalAny(
            [
                "You are already casting a spell.",
                "You must wait before casting another spell.",
            ]
        )

    def _checkNoSpell(self):
        return API.InJournalAny(
            ["You do not have that spell!", "You have not learned that spell"]
        )

    def _checkFizzleJournal(self):
        return API.InJournalAny(
            [
                "You lost your concentration.",
                "Your spell fizzles.",
                "You can't cast that spell right now.",
                "You fail to cast",
                "Something is blocking the location.",
            ]
        )

    def _checkManaFailureJournal(self):
        return API.InJournalAny(["You don't have enough mana"])

    def _getRecallMethod(self):
        magery = API.GetSkill("Magery").Value
        chivalry = API.GetSkill("Chivalry").Value
        if magery >= 40:
            return "magery"
        elif chivalry >= 40:
            return "chivalry"
        return None

    def _waitForRecovery(self, timeout=2.0):
        start = self._now()
        while self._now() - start < timeout:
            if not self._checkRecoveredJournal():
                return True
            API.Pause(0.05)
        return False


# =========== End of _Utils\Magic.py ============#


# =========== Start of _Utils\Color.py ============#
class Color:
    defaultRed = "#b80028"
    defaultGreen = "#00b828"
    defaultLightGray = "#b8b8c0"
    defaultGray = "#585858"
    defaultBlack = "#000000"
    defaultWhite = "#f8f8f8"
    defaultBorder = "#a87000"

    colors = [
        {"hue": 68, "rgb": [24, 232, 0], "hex": "#18e800"},
        {"hue": 88, "rgb": [0, 208, 232], "hex": "#00d0e8"},
        {"hue": 1, "rgb": [0, 0, 8], "hex": "#000008"},
        {"hue": 2, "rgb": [0, 0, 184], "hex": "#0000b8"},
        {"hue": 98798, "rgb": [0, 0, 232], "hex": "#0000e8"},
        {"hue": 4, "rgb": [48, 48, 232], "hex": "#3030e8"},
        {"hue": 5, "rgb": [96, 96, 240], "hex": "#6060f0"},
        {"hue": 6, "rgb": [144, 144, 240], "hex": "#9090f0"},
        {"hue": 7, "rgb": [56, 0, 184], "hex": "#3800b8"},
        {"hue": 8, "rgb": [72, 0, 232], "hex": "#4800e8"},
        {"hue": 9, "rgb": [104, 48, 232], "hex": "#6830e8"},
        {"hue": 10, "rgb": [144, 96, 240], "hex": "#9060f0"},
        {"hue": 11, "rgb": [176, 144, 240], "hex": "#b090f0"},
        {"hue": 12, "rgb": [104, 0, 184], "hex": "#6800b8"},
        {"hue": 13, "rgb": [136, 0, 232], "hex": "#8800e8"},
        {"hue": 14, "rgb": [160, 48, 232], "hex": "#a030e8"},
        {"hue": 15, "rgb": [176, 96, 240], "hex": "#b060f0"},
        {"hue": 16, "rgb": [200, 144, 240], "hex": "#c890f0"},
        {"hue": 17, "rgb": [160, 0, 184], "hex": "#a000b8"},
        {"hue": 18, "rgb": [208, 0, 232], "hex": "#d000e8"},
        {"hue": 19, "rgb": [216, 48, 232], "hex": "#d830e8"},
        {"hue": 20, "rgb": [224, 96, 240], "hex": "#e060f0"},
        {"hue": 21, "rgb": [232, 144, 240], "hex": "#e890f0"},
        {"hue": 22, "rgb": [184, 0, 144], "hex": "#b80090"},
        {"hue": 23, "rgb": [232, 0, 184], "hex": "#e800b8"},
        {"hue": 24, "rgb": [232, 48, 192], "hex": "#e830c0"},
        {"hue": 25, "rgb": [240, 96, 208], "hex": "#f060d0"},
        {"hue": 26, "rgb": [240, 144, 216], "hex": "#f090d8"},
        {"hue": 27, "rgb": [184, 0, 88], "hex": "#b80058"},
        {"hue": 28, "rgb": [232, 0, 112], "hex": "#e80070"},
        {"hue": 29, "rgb": [232, 48, 144], "hex": "#e83090"},
        {"hue": 30, "rgb": [240, 96, 168], "hex": "#f060a8"},
        {"hue": 31, "rgb": [240, 144, 192], "hex": "#f090c0"},
        {"hue": 32, "rgb": [184, 0, 40], "hex": "#b80028"},
        {"hue": 33, "rgb": [232, 0, 48], "hex": "#e80030"},
        {"hue": 34, "rgb": [232, 48, 88], "hex": "#e83058"},
        {"hue": 35, "rgb": [240, 96, 128], "hex": "#f06080"},
        {"hue": 36, "rgb": [240, 144, 168], "hex": "#f090a8"},
        {"hue": 37, "rgb": [184, 16, 0], "hex": "#b81000"},
        {"hue": 38, "rgb": [232, 24, 0], "hex": "#e81800"},
        {"hue": 39, "rgb": [232, 72, 48], "hex": "#e84830"},
        {"hue": 40, "rgb": [240, 112, 96], "hex": "#f07060"},
        {"hue": 41, "rgb": [240, 160, 144], "hex": "#f0a090"},
        {"hue": 42, "rgb": [184, 72, 0], "hex": "#b84800"},
        {"hue": 43, "rgb": [232, 96, 0], "hex": "#e86000"},
        {"hue": 44, "rgb": [232, 128, 48], "hex": "#e88030"},
        {"hue": 45, "rgb": [240, 152, 96], "hex": "#f09860"},
        {"hue": 46, "rgb": [240, 184, 144], "hex": "#f0b890"},
        {"hue": 47, "rgb": [184, 128, 0], "hex": "#b88000"},
        {"hue": 48, "rgb": [232, 160, 0], "hex": "#e8a000"},
        {"hue": 49, "rgb": [232, 176, 48], "hex": "#e8b030"},
        {"hue": 50, "rgb": [240, 192, 96], "hex": "#f0c060"},
        {"hue": 51, "rgb": [240, 208, 144], "hex": "#f0d090"},
        {"hue": 52, "rgb": [184, 184, 0], "hex": "#b8b800"},
        {"hue": 53, "rgb": [232, 232, 0], "hex": "#e8e800"},
        {"hue": 54, "rgb": [232, 232, 48], "hex": "#e8e830"},
        {"hue": 55, "rgb": [240, 240, 96], "hex": "#f0f060"},
        {"hue": 56, "rgb": [240, 240, 144], "hex": "#f0f090"},
        {"hue": 57, "rgb": [128, 184, 0], "hex": "#80b800"},
        {"hue": 58, "rgb": [160, 232, 0], "hex": "#a0e800"},
        {"hue": 59, "rgb": [176, 232, 48], "hex": "#b0e830"},
        {"hue": 60, "rgb": [192, 240, 96], "hex": "#c0f060"},
        {"hue": 61, "rgb": [208, 240, 144], "hex": "#d0f090"},
        {"hue": 62, "rgb": [72, 184, 0], "hex": "#48b800"},
        {"hue": 63, "rgb": [96, 232, 0], "hex": "#60e800"},
        {"hue": 64, "rgb": [128, 232, 48], "hex": "#80e830"},
        {"hue": 65, "rgb": [152, 240, 96], "hex": "#98f060"},
        {"hue": 66, "rgb": [184, 240, 144], "hex": "#b8f090"},
        {"hue": 67, "rgb": [16, 184, 0], "hex": "#10b800"},
        {"hue": 68, "rgb": [24, 232, 0], "hex": "#18e800"},
        {"hue": 69, "rgb": [72, 232, 48], "hex": "#48e830"},
        {"hue": 70, "rgb": [112, 240, 96], "hex": "#70f060"},
        {"hue": 71, "rgb": [160, 240, 144], "hex": "#a0f090"},
        {"hue": 72, "rgb": [0, 184, 40], "hex": "#00b828"},
        {"hue": 73, "rgb": [0, 232, 48], "hex": "#00e830"},
        {"hue": 74, "rgb": [48, 232, 88], "hex": "#30e858"},
        {"hue": 75, "rgb": [96, 240, 128], "hex": "#60f080"},
        {"hue": 76, "rgb": [144, 240, 168], "hex": "#90f0a8"},
        {"hue": 77, "rgb": [0, 184, 88], "hex": "#00b858"},
        {"hue": 78, "rgb": [0, 232, 120], "hex": "#00e878"},
        {"hue": 79, "rgb": [48, 232, 144], "hex": "#30e890"},
        {"hue": 80, "rgb": [96, 240, 168], "hex": "#60f0a8"},
        {"hue": 81, "rgb": [144, 240, 192], "hex": "#90f0c0"},
        {"hue": 82, "rgb": [0, 184, 144], "hex": "#00b890"},
        {"hue": 83, "rgb": [0, 232, 184], "hex": "#00e8b8"},
        {"hue": 84, "rgb": [48, 232, 192], "hex": "#30e8c0"},
        {"hue": 85, "rgb": [96, 240, 208], "hex": "#60f0d0"},
        {"hue": 86, "rgb": [144, 240, 216], "hex": "#90f0d8"},
        {"hue": 87, "rgb": [0, 160, 184], "hex": "#00a0b8"},
        {"hue": 88, "rgb": [0, 208, 232], "hex": "#00d0e8"},
        {"hue": 89, "rgb": [48, 216, 232], "hex": "#30d8e8"},
        {"hue": 90, "rgb": [96, 224, 240], "hex": "#60e0f0"},
        {"hue": 91, "rgb": [144, 232, 240], "hex": "#90e8f0"},
        {"hue": 92, "rgb": [0, 104, 184], "hex": "#0068b8"},
        {"hue": 93, "rgb": [0, 136, 232], "hex": "#0088e8"},
        {"hue": 94, "rgb": [48, 160, 232], "hex": "#30a0e8"},
        {"hue": 95, "rgb": [96, 176, 240], "hex": "#60b0f0"},
        {"hue": 96, "rgb": [144, 200, 240], "hex": "#90c8f0"},
        {"hue": 97, "rgb": [0, 56, 184], "hex": "#0038b8"},
        {"hue": 98, "rgb": [0, 72, 232], "hex": "#0048e8"},
        {"hue": 99, "rgb": [48, 104, 232], "hex": "#3068e8"},
        {"hue": 100, "rgb": [96, 144, 240], "hex": "#6090f0"},
        {"hue": 101, "rgb": [144, 176, 240], "hex": "#90b0f0"},
        {"hue": 102, "rgb": [8, 8, 176], "hex": "#0808b0"},
        {"hue": 103, "rgb": [16, 16, 216], "hex": "#1010d8"},
        {"hue": 104, "rgb": [56, 56, 224], "hex": "#3838e0"},
        {"hue": 105, "rgb": [104, 104, 232], "hex": "#6868e8"},
        {"hue": 106, "rgb": [152, 152, 232], "hex": "#9898e8"},
        {"hue": 107, "rgb": [64, 8, 176], "hex": "#4008b0"},
        {"hue": 108, "rgb": [80, 16, 216], "hex": "#5010d8"},
        {"hue": 109, "rgb": [112, 56, 224], "hex": "#7038e0"},
        {"hue": 110, "rgb": [144, 104, 232], "hex": "#9068e8"},
        {"hue": 111, "rgb": [176, 152, 232], "hex": "#b098e8"},
        {"hue": 112, "rgb": [104, 8, 176], "hex": "#6808b0"},
        {"hue": 113, "rgb": [136, 16, 216], "hex": "#8810d8"},
        {"hue": 114, "rgb": [160, 56, 224], "hex": "#a038e0"},
        {"hue": 115, "rgb": [176, 104, 232], "hex": "#b068e8"},
        {"hue": 116, "rgb": [200, 152, 232], "hex": "#c898e8"},
        {"hue": 117, "rgb": [152, 8, 176], "hex": "#9808b0"},
        {"hue": 118, "rgb": [192, 16, 216], "hex": "#c010d8"},
        {"hue": 119, "rgb": [208, 56, 224], "hex": "#d038e0"},
        {"hue": 120, "rgb": [216, 104, 232], "hex": "#d868e8"},
        {"hue": 121, "rgb": [224, 152, 232], "hex": "#e098e8"},
        {"hue": 122, "rgb": [176, 8, 136], "hex": "#b00888"},
        {"hue": 123, "rgb": [216, 16, 176], "hex": "#d810b0"},
        {"hue": 124, "rgb": [224, 56, 184], "hex": "#e038b8"},
        {"hue": 125, "rgb": [232, 104, 200], "hex": "#e868c8"},
        {"hue": 126, "rgb": [232, 152, 216], "hex": "#e898d8"},
        {"hue": 127, "rgb": [176, 8, 88], "hex": "#b00858"},
        {"hue": 128, "rgb": [216, 16, 112], "hex": "#d81070"},
        {"hue": 129, "rgb": [224, 56, 144], "hex": "#e03890"},
        {"hue": 130, "rgb": [232, 104, 168], "hex": "#e868a8"},
        {"hue": 131, "rgb": [232, 152, 192], "hex": "#e898c0"},
        {"hue": 132, "rgb": [176, 8, 48], "hex": "#b00830"},
        {"hue": 133, "rgb": [216, 16, 56], "hex": "#d81038"},
        {"hue": 134, "rgb": [224, 56, 96], "hex": "#e03860"},
        {"hue": 135, "rgb": [232, 104, 136], "hex": "#e86888"},
        {"hue": 136, "rgb": [232, 152, 168], "hex": "#e898a8"},
        {"hue": 137, "rgb": [176, 24, 8], "hex": "#b01808"},
        {"hue": 138, "rgb": [216, 40, 16], "hex": "#d82810"},
        {"hue": 139, "rgb": [224, 80, 56], "hex": "#e05038"},
        {"hue": 140, "rgb": [232, 120, 104], "hex": "#e87868"},
        {"hue": 141, "rgb": [232, 160, 152], "hex": "#e8a098"},
        {"hue": 142, "rgb": [176, 72, 8], "hex": "#b04808"},
        {"hue": 143, "rgb": [216, 96, 16], "hex": "#d86010"},
        {"hue": 144, "rgb": [224, 128, 56], "hex": "#e08038"},
        {"hue": 145, "rgb": [232, 160, 104], "hex": "#e8a068"},
        {"hue": 146, "rgb": [232, 184, 152], "hex": "#e8b898"},
        {"hue": 147, "rgb": [176, 120, 8], "hex": "#b07808"},
        {"hue": 148, "rgb": [216, 152, 16], "hex": "#d89810"},
        {"hue": 149, "rgb": [224, 168, 56], "hex": "#e0a838"},
        {"hue": 150, "rgb": [232, 192, 104], "hex": "#e8c068"},
        {"hue": 151, "rgb": [232, 208, 152], "hex": "#e8d098"},
        {"hue": 152, "rgb": [176, 176, 8], "hex": "#b0b008"},
        {"hue": 153, "rgb": [216, 216, 16], "hex": "#d8d810"},
        {"hue": 154, "rgb": [224, 224, 56], "hex": "#e0e038"},
        {"hue": 155, "rgb": [232, 232, 104], "hex": "#e8e868"},
        {"hue": 156, "rgb": [232, 232, 152], "hex": "#e8e898"},
        {"hue": 157, "rgb": [120, 176, 8], "hex": "#78b008"},
        {"hue": 158, "rgb": [152, 216, 16], "hex": "#98d810"},
        {"hue": 159, "rgb": [168, 224, 56], "hex": "#a8e038"},
        {"hue": 160, "rgb": [192, 232, 104], "hex": "#c0e868"},
        {"hue": 161, "rgb": [208, 232, 152], "hex": "#d0e898"},
        {"hue": 162, "rgb": [72, 176, 8], "hex": "#48b008"},
        {"hue": 163, "rgb": [96, 216, 16], "hex": "#60d810"},
        {"hue": 164, "rgb": [128, 224, 56], "hex": "#80e038"},
        {"hue": 165, "rgb": [160, 232, 104], "hex": "#a0e868"},
        {"hue": 166, "rgb": [184, 232, 152], "hex": "#b8e898"},
        {"hue": 167, "rgb": [24, 176, 8], "hex": "#18b008"},
        {"hue": 168, "rgb": [40, 216, 16], "hex": "#28d810"},
        {"hue": 169, "rgb": [80, 224, 56], "hex": "#50e038"},
        {"hue": 170, "rgb": [120, 232, 104], "hex": "#78e868"},
        {"hue": 171, "rgb": [160, 232, 152], "hex": "#a0e898"},
        {"hue": 172, "rgb": [8, 176, 48], "hex": "#08b030"},
        {"hue": 173, "rgb": [16, 216, 56], "hex": "#10d838"},
        {"hue": 174, "rgb": [56, 224, 96], "hex": "#38e060"},
        {"hue": 175, "rgb": [104, 232, 136], "hex": "#68e888"},
        {"hue": 176, "rgb": [152, 232, 168], "hex": "#98e8a8"},
        {"hue": 177, "rgb": [8, 176, 88], "hex": "#08b058"},
        {"hue": 178, "rgb": [16, 216, 120], "hex": "#10d878"},
        {"hue": 179, "rgb": [56, 224, 144], "hex": "#38e090"},
        {"hue": 180, "rgb": [104, 232, 168], "hex": "#68e8a8"},
        {"hue": 181, "rgb": [152, 232, 192], "hex": "#98e8c0"},
        {"hue": 182, "rgb": [8, 176, 136], "hex": "#08b088"},
        {"hue": 183, "rgb": [16, 216, 176], "hex": "#10d8b0"},
        {"hue": 184, "rgb": [56, 224, 184], "hex": "#38e0b8"},
        {"hue": 185, "rgb": [104, 232, 200], "hex": "#68e8c8"},
        {"hue": 186, "rgb": [152, 232, 216], "hex": "#98e8d8"},
        {"hue": 187, "rgb": [8, 152, 176], "hex": "#0898b0"},
        {"hue": 188, "rgb": [16, 192, 216], "hex": "#10c0d8"},
        {"hue": 189, "rgb": [56, 208, 224], "hex": "#38d0e0"},
        {"hue": 190, "rgb": [104, 216, 232], "hex": "#68d8e8"},
        {"hue": 191, "rgb": [152, 224, 232], "hex": "#98e0e8"},
        {"hue": 192, "rgb": [8, 104, 176], "hex": "#0868b0"},
        {"hue": 193, "rgb": [16, 136, 216], "hex": "#1088d8"},
        {"hue": 194, "rgb": [56, 160, 224], "hex": "#38a0e0"},
        {"hue": 195, "rgb": [104, 176, 232], "hex": "#68b0e8"},
        {"hue": 196, "rgb": [152, 200, 232], "hex": "#98c8e8"},
        {"hue": 197, "rgb": [8, 64, 176], "hex": "#0840b0"},
        {"hue": 198, "rgb": [16, 80, 216], "hex": "#1050d8"},
        {"hue": 199, "rgb": [56, 112, 224], "hex": "#3870e0"},
        {"hue": 200, "rgb": [104, 144, 232], "hex": "#6890e8"},
        {"hue": 201, "rgb": [152, 176, 232], "hex": "#98b0e8"},
        {"hue": 202, "rgb": [16, 16, 160], "hex": "#1010a0"},
        {"hue": 203, "rgb": [24, 24, 208], "hex": "#1818d0"},
        {"hue": 204, "rgb": [72, 72, 216], "hex": "#4848d8"},
        {"hue": 205, "rgb": [112, 112, 224], "hex": "#7070e0"},
        {"hue": 206, "rgb": [160, 160, 232], "hex": "#a0a0e8"},
        {"hue": 207, "rgb": [64, 16, 160], "hex": "#4010a0"},
        {"hue": 208, "rgb": [80, 24, 208], "hex": "#5018d0"},
        {"hue": 209, "rgb": [112, 72, 216], "hex": "#7048d8"},
        {"hue": 210, "rgb": [144, 112, 224], "hex": "#9070e0"},
        {"hue": 211, "rgb": [176, 160, 232], "hex": "#b0a0e8"},
        {"hue": 212, "rgb": [104, 16, 160], "hex": "#6810a0"},
        {"hue": 213, "rgb": [136, 24, 208], "hex": "#8818d0"},
        {"hue": 214, "rgb": [152, 72, 216], "hex": "#9848d8"},
        {"hue": 215, "rgb": [176, 112, 224], "hex": "#b070e0"},
        {"hue": 216, "rgb": [200, 160, 232], "hex": "#c8a0e8"},
        {"hue": 217, "rgb": [144, 16, 160], "hex": "#9010a0"},
        {"hue": 218, "rgb": [184, 24, 208], "hex": "#b818d0"},
        {"hue": 219, "rgb": [200, 72, 216], "hex": "#c848d8"},
        {"hue": 220, "rgb": [208, 112, 224], "hex": "#d070e0"},
        {"hue": 221, "rgb": [224, 160, 232], "hex": "#e0a0e8"},
        {"hue": 222, "rgb": [160, 16, 128], "hex": "#a01080"},
        {"hue": 223, "rgb": [208, 24, 168], "hex": "#d018a8"},
        {"hue": 224, "rgb": [216, 72, 184], "hex": "#d848b8"},
        {"hue": 225, "rgb": [224, 112, 200], "hex": "#e070c8"},
        {"hue": 226, "rgb": [232, 160, 216], "hex": "#e8a0d8"},
        {"hue": 227, "rgb": [160, 16, 88], "hex": "#a01058"},
        {"hue": 228, "rgb": [208, 24, 112], "hex": "#d01870"},
        {"hue": 229, "rgb": [216, 72, 144], "hex": "#d84890"},
        {"hue": 230, "rgb": [224, 112, 168], "hex": "#e070a8"},
        {"hue": 231, "rgb": [232, 160, 192], "hex": "#e8a0c0"},
        {"hue": 232, "rgb": [160, 16, 48], "hex": "#a01030"},
        {"hue": 233, "rgb": [208, 24, 64], "hex": "#d01840"},
        {"hue": 234, "rgb": [216, 72, 104], "hex": "#d84868"},
        {"hue": 235, "rgb": [224, 112, 136], "hex": "#e07088"},
        {"hue": 236, "rgb": [232, 160, 176], "hex": "#e8a0b0"},
        {"hue": 237, "rgb": [160, 32, 16], "hex": "#a02010"},
        {"hue": 238, "rgb": [208, 48, 24], "hex": "#d03018"},
        {"hue": 239, "rgb": [216, 88, 72], "hex": "#d85848"},
        {"hue": 240, "rgb": [224, 128, 112], "hex": "#e08070"},
        {"hue": 241, "rgb": [232, 168, 160], "hex": "#e8a8a0"},
        {"hue": 242, "rgb": [160, 80, 16], "hex": "#a05010"},
        {"hue": 243, "rgb": [208, 96, 24], "hex": "#d06018"},
        {"hue": 244, "rgb": [216, 128, 72], "hex": "#d88048"},
        {"hue": 245, "rgb": [224, 160, 112], "hex": "#e0a070"},
        {"hue": 246, "rgb": [232, 184, 160], "hex": "#e8b8a0"},
        {"hue": 247, "rgb": [160, 120, 16], "hex": "#a07810"},
        {"hue": 248, "rgb": [208, 152, 24], "hex": "#d09818"},
        {"hue": 249, "rgb": [216, 168, 72], "hex": "#d8a848"},
        {"hue": 250, "rgb": [224, 184, 112], "hex": "#e0b870"},
        {"hue": 251, "rgb": [232, 208, 160], "hex": "#e8d0a0"},
        {"hue": 252, "rgb": [160, 160, 16], "hex": "#a0a010"},
        {"hue": 253, "rgb": [208, 208, 24], "hex": "#d0d018"},
        {"hue": 254, "rgb": [216, 216, 72], "hex": "#d8d848"},
        {"hue": 255, "rgb": [224, 224, 112], "hex": "#e0e070"},
        {"hue": 256, "rgb": [232, 232, 160], "hex": "#e8e8a0"},
        {"hue": 257, "rgb": [120, 160, 16], "hex": "#78a010"},
        {"hue": 258, "rgb": [152, 208, 24], "hex": "#98d018"},
        {"hue": 259, "rgb": [168, 216, 72], "hex": "#a8d848"},
        {"hue": 260, "rgb": [184, 224, 112], "hex": "#b8e070"},
        {"hue": 261, "rgb": [208, 232, 160], "hex": "#d0e8a0"},
        {"hue": 262, "rgb": [80, 160, 16], "hex": "#50a010"},
        {"hue": 263, "rgb": [96, 208, 24], "hex": "#60d018"},
        {"hue": 264, "rgb": [128, 216, 72], "hex": "#80d848"},
        {"hue": 265, "rgb": [160, 224, 112], "hex": "#a0e070"},
        {"hue": 266, "rgb": [184, 232, 160], "hex": "#b8e8a0"},
        {"hue": 267, "rgb": [32, 160, 16], "hex": "#20a010"},
        {"hue": 268, "rgb": [48, 208, 24], "hex": "#30d018"},
        {"hue": 269, "rgb": [88, 216, 72], "hex": "#58d848"},
        {"hue": 270, "rgb": [128, 224, 112], "hex": "#80e070"},
        {"hue": 271, "rgb": [168, 232, 160], "hex": "#a8e8a0"},
        {"hue": 272, "rgb": [16, 160, 48], "hex": "#10a030"},
        {"hue": 273, "rgb": [24, 208, 64], "hex": "#18d040"},
        {"hue": 274, "rgb": [72, 216, 104], "hex": "#48d868"},
        {"hue": 275, "rgb": [112, 224, 136], "hex": "#70e088"},
        {"hue": 276, "rgb": [160, 232, 176], "hex": "#a0e8b0"},
        {"hue": 277, "rgb": [16, 160, 88], "hex": "#10a058"},
        {"hue": 278, "rgb": [24, 208, 120], "hex": "#18d078"},
        {"hue": 279, "rgb": [72, 216, 144], "hex": "#48d890"},
        {"hue": 280, "rgb": [112, 224, 168], "hex": "#70e0a8"},
        {"hue": 281, "rgb": [160, 232, 192], "hex": "#a0e8c0"},
        {"hue": 282, "rgb": [16, 160, 128], "hex": "#10a080"},
        {"hue": 283, "rgb": [24, 208, 168], "hex": "#18d0a8"},
        {"hue": 284, "rgb": [72, 216, 184], "hex": "#48d8b8"},
        {"hue": 285, "rgb": [112, 224, 200], "hex": "#70e0c8"},
        {"hue": 286, "rgb": [160, 232, 216], "hex": "#a0e8d8"},
        {"hue": 287, "rgb": [16, 144, 160], "hex": "#1090a0"},
        {"hue": 288, "rgb": [24, 184, 208], "hex": "#18b8d0"},
        {"hue": 289, "rgb": [72, 200, 216], "hex": "#48c8d8"},
        {"hue": 290, "rgb": [112, 208, 224], "hex": "#70d0e0"},
        {"hue": 291, "rgb": [160, 224, 232], "hex": "#a0e0e8"},
        {"hue": 292, "rgb": [16, 104, 160], "hex": "#1068a0"},
        {"hue": 293, "rgb": [24, 136, 208], "hex": "#1888d0"},
        {"hue": 294, "rgb": [72, 152, 216], "hex": "#4898d8"},
        {"hue": 295, "rgb": [112, 176, 224], "hex": "#70b0e0"},
        {"hue": 296, "rgb": [160, 200, 232], "hex": "#a0c8e8"},
        {"hue": 297, "rgb": [16, 64, 160], "hex": "#1040a0"},
        {"hue": 298, "rgb": [24, 80, 208], "hex": "#1850d0"},
        {"hue": 299, "rgb": [72, 112, 216], "hex": "#4870d8"},
        {"hue": 300, "rgb": [112, 144, 224], "hex": "#7090e0"},
        {"hue": 301, "rgb": [160, 176, 232], "hex": "#a0b0e8"},
        {"hue": 302, "rgb": [32, 32, 152], "hex": "#202098"},
        {"hue": 303, "rgb": [40, 40, 192], "hex": "#2828c0"},
        {"hue": 304, "rgb": [80, 80, 200], "hex": "#5050c8"},
        {"hue": 305, "rgb": [120, 120, 216], "hex": "#7878d8"},
        {"hue": 306, "rgb": [160, 160, 224], "hex": "#a0a0e0"},
        {"hue": 307, "rgb": [64, 32, 152], "hex": "#402098"},
        {"hue": 308, "rgb": [88, 40, 192], "hex": "#5828c0"},
        {"hue": 309, "rgb": [120, 80, 200], "hex": "#7850c8"},
        {"hue": 310, "rgb": [152, 120, 216], "hex": "#9878d8"},
        {"hue": 311, "rgb": [184, 160, 224], "hex": "#b8a0e0"},
        {"hue": 312, "rgb": [104, 32, 152], "hex": "#682098"},
        {"hue": 313, "rgb": [128, 40, 192], "hex": "#8028c0"},
        {"hue": 314, "rgb": [152, 80, 200], "hex": "#9850c8"},
        {"hue": 315, "rgb": [176, 120, 216], "hex": "#b078d8"},
        {"hue": 316, "rgb": [200, 160, 224], "hex": "#c8a0e0"},
        {"hue": 317, "rgb": [136, 32, 152], "hex": "#882098"},
        {"hue": 318, "rgb": [176, 40, 192], "hex": "#b028c0"},
        {"hue": 319, "rgb": [192, 80, 200], "hex": "#c050c8"},
        {"hue": 320, "rgb": [200, 120, 216], "hex": "#c878d8"},
        {"hue": 321, "rgb": [216, 160, 224], "hex": "#d8a0e0"},
        {"hue": 322, "rgb": [152, 32, 128], "hex": "#982080"},
        {"hue": 323, "rgb": [192, 40, 160], "hex": "#c028a0"},
        {"hue": 324, "rgb": [200, 80, 176], "hex": "#c850b0"},
        {"hue": 325, "rgb": [216, 120, 192], "hex": "#d878c0"},
        {"hue": 326, "rgb": [224, 160, 208], "hex": "#e0a0d0"},
        {"hue": 327, "rgb": [152, 32, 88], "hex": "#982058"},
        {"hue": 328, "rgb": [192, 40, 112], "hex": "#c02870"},
        {"hue": 329, "rgb": [200, 80, 144], "hex": "#c85090"},
        {"hue": 330, "rgb": [216, 120, 168], "hex": "#d878a8"},
        {"hue": 331, "rgb": [224, 160, 192], "hex": "#e0a0c0"},
        {"hue": 332, "rgb": [152, 32, 56], "hex": "#982038"},
        {"hue": 333, "rgb": [192, 40, 72], "hex": "#c02848"},
        {"hue": 334, "rgb": [200, 80, 104], "hex": "#c85068"},
        {"hue": 335, "rgb": [216, 120, 144], "hex": "#d87890"},
        {"hue": 336, "rgb": [224, 160, 176], "hex": "#e0a0b0"},
        {"hue": 337, "rgb": [152, 40, 32], "hex": "#982820"},
        {"hue": 338, "rgb": [192, 56, 40], "hex": "#c03828"},
        {"hue": 339, "rgb": [200, 96, 80], "hex": "#c86050"},
        {"hue": 340, "rgb": [216, 128, 120], "hex": "#d88078"},
        {"hue": 341, "rgb": [224, 168, 160], "hex": "#e0a8a0"},
        {"hue": 342, "rgb": [152, 80, 32], "hex": "#985020"},
        {"hue": 343, "rgb": [192, 104, 40], "hex": "#c06828"},
        {"hue": 344, "rgb": [200, 128, 80], "hex": "#c88050"},
        {"hue": 345, "rgb": [216, 160, 120], "hex": "#d8a078"},
        {"hue": 346, "rgb": [224, 184, 160], "hex": "#e0b8a0"},
        {"hue": 347, "rgb": [152, 112, 32], "hex": "#987020"},
        {"hue": 348, "rgb": [192, 144, 40], "hex": "#c09028"},
        {"hue": 349, "rgb": [200, 168, 80], "hex": "#c8a850"},
        {"hue": 350, "rgb": [216, 184, 120], "hex": "#d8b878"},
        {"hue": 351, "rgb": [224, 208, 160], "hex": "#e0d0a0"},
        {"hue": 352, "rgb": [152, 152, 32], "hex": "#989820"},
        {"hue": 353, "rgb": [192, 192, 40], "hex": "#c0c028"},
        {"hue": 354, "rgb": [200, 200, 80], "hex": "#c8c850"},
        {"hue": 355, "rgb": [216, 216, 120], "hex": "#d8d878"},
        {"hue": 356, "rgb": [224, 224, 160], "hex": "#e0e0a0"},
        {"hue": 357, "rgb": [112, 152, 32], "hex": "#709820"},
        {"hue": 358, "rgb": [144, 192, 40], "hex": "#90c028"},
        {"hue": 359, "rgb": [168, 200, 80], "hex": "#a8c850"},
        {"hue": 360, "rgb": [184, 216, 120], "hex": "#b8d878"},
        {"hue": 361, "rgb": [208, 224, 160], "hex": "#d0e0a0"},
        {"hue": 362, "rgb": [80, 152, 32], "hex": "#509820"},
        {"hue": 363, "rgb": [104, 192, 40], "hex": "#68c028"},
        {"hue": 364, "rgb": [128, 200, 80], "hex": "#80c850"},
        {"hue": 365, "rgb": [160, 216, 120], "hex": "#a0d878"},
        {"hue": 366, "rgb": [184, 224, 160], "hex": "#b8e0a0"},
        {"hue": 367, "rgb": [40, 152, 32], "hex": "#289820"},
        {"hue": 368, "rgb": [56, 192, 40], "hex": "#38c028"},
        {"hue": 369, "rgb": [96, 200, 80], "hex": "#60c850"},
        {"hue": 370, "rgb": [128, 216, 120], "hex": "#80d878"},
        {"hue": 371, "rgb": [168, 224, 160], "hex": "#a8e0a0"},
        {"hue": 372, "rgb": [32, 152, 56], "hex": "#209838"},
        {"hue": 373, "rgb": [40, 192, 72], "hex": "#28c048"},
        {"hue": 374, "rgb": [80, 200, 104], "hex": "#50c868"},
        {"hue": 375, "rgb": [120, 216, 144], "hex": "#78d890"},
        {"hue": 376, "rgb": [160, 224, 176], "hex": "#a0e0b0"},
        {"hue": 377, "rgb": [32, 152, 88], "hex": "#209858"},
        {"hue": 378, "rgb": [40, 192, 120], "hex": "#28c078"},
        {"hue": 379, "rgb": [80, 200, 144], "hex": "#50c890"},
        {"hue": 380, "rgb": [120, 216, 168], "hex": "#78d8a8"},
        {"hue": 381, "rgb": [160, 224, 192], "hex": "#a0e0c0"},
        {"hue": 382, "rgb": [32, 152, 128], "hex": "#209880"},
        {"hue": 383, "rgb": [40, 192, 160], "hex": "#28c0a0"},
        {"hue": 384, "rgb": [80, 200, 176], "hex": "#50c8b0"},
        {"hue": 385, "rgb": [120, 216, 192], "hex": "#78d8c0"},
        {"hue": 386, "rgb": [160, 224, 208], "hex": "#a0e0d0"},
        {"hue": 387, "rgb": [32, 136, 152], "hex": "#208898"},
        {"hue": 388, "rgb": [40, 176, 192], "hex": "#28b0c0"},
        {"hue": 389, "rgb": [80, 192, 200], "hex": "#50c0c8"},
        {"hue": 390, "rgb": [120, 200, 216], "hex": "#78c8d8"},
        {"hue": 391, "rgb": [160, 216, 224], "hex": "#a0d8e0"},
        {"hue": 392, "rgb": [32, 104, 152], "hex": "#206898"},
        {"hue": 393, "rgb": [40, 128, 192], "hex": "#2880c0"},
        {"hue": 394, "rgb": [80, 152, 200], "hex": "#5098c8"},
        {"hue": 395, "rgb": [120, 176, 216], "hex": "#78b0d8"},
        {"hue": 396, "rgb": [160, 200, 224], "hex": "#a0c8e0"},
        {"hue": 397, "rgb": [32, 64, 152], "hex": "#204098"},
        {"hue": 398, "rgb": [40, 88, 192], "hex": "#2858c0"},
        {"hue": 399, "rgb": [80, 120, 200], "hex": "#5078c8"},
        {"hue": 400, "rgb": [120, 152, 216], "hex": "#7898d8"},
        {"hue": 401, "rgb": [160, 184, 224], "hex": "#a0b8e0"},
        {"hue": 402, "rgb": [40, 40, 144], "hex": "#282890"},
        {"hue": 403, "rgb": [48, 48, 184], "hex": "#3030b8"},
        {"hue": 404, "rgb": [88, 88, 192], "hex": "#5858c0"},
        {"hue": 405, "rgb": [128, 128, 208], "hex": "#8080d0"},
        {"hue": 406, "rgb": [168, 168, 216], "hex": "#a8a8d8"},
        {"hue": 407, "rgb": [72, 40, 144], "hex": "#482890"},
        {"hue": 408, "rgb": [96, 48, 184], "hex": "#6030b8"},
        {"hue": 409, "rgb": [120, 88, 192], "hex": "#7858c0"},
        {"hue": 410, "rgb": [152, 128, 208], "hex": "#9880d0"},
        {"hue": 411, "rgb": [184, 168, 216], "hex": "#b8a8d8"},
        {"hue": 412, "rgb": [96, 40, 144], "hex": "#602890"},
        {"hue": 413, "rgb": [128, 48, 184], "hex": "#8030b8"},
        {"hue": 414, "rgb": [152, 88, 192], "hex": "#9858c0"},
        {"hue": 415, "rgb": [176, 128, 208], "hex": "#b080d0"},
        {"hue": 416, "rgb": [200, 168, 216], "hex": "#c8a8d8"},
        {"hue": 417, "rgb": [128, 40, 144], "hex": "#802890"},
        {"hue": 418, "rgb": [168, 48, 184], "hex": "#a830b8"},
        {"hue": 419, "rgb": [184, 88, 192], "hex": "#b858c0"},
        {"hue": 420, "rgb": [200, 128, 208], "hex": "#c880d0"},
        {"hue": 421, "rgb": [216, 168, 216], "hex": "#d8a8d8"},
        {"hue": 422, "rgb": [144, 40, 120], "hex": "#902878"},
        {"hue": 423, "rgb": [184, 48, 152], "hex": "#b83098"},
        {"hue": 424, "rgb": [192, 88, 168], "hex": "#c058a8"},
        {"hue": 425, "rgb": [208, 128, 192], "hex": "#d080c0"},
        {"hue": 426, "rgb": [216, 168, 208], "hex": "#d8a8d0"},
        {"hue": 427, "rgb": [144, 40, 88], "hex": "#902858"},
        {"hue": 428, "rgb": [184, 48, 112], "hex": "#b83070"},
        {"hue": 429, "rgb": [192, 88, 144], "hex": "#c05890"},
        {"hue": 430, "rgb": [208, 128, 168], "hex": "#d080a8"},
        {"hue": 431, "rgb": [216, 168, 192], "hex": "#d8a8c0"},
        {"hue": 432, "rgb": [144, 40, 64], "hex": "#902840"},
        {"hue": 433, "rgb": [184, 48, 80], "hex": "#b83050"},
        {"hue": 434, "rgb": [192, 88, 112], "hex": "#c05870"},
        {"hue": 435, "rgb": [208, 128, 144], "hex": "#d08090"},
        {"hue": 436, "rgb": [216, 168, 176], "hex": "#d8a8b0"},
        {"hue": 437, "rgb": [144, 48, 40], "hex": "#903028"},
        {"hue": 438, "rgb": [184, 64, 48], "hex": "#b84030"},
        {"hue": 439, "rgb": [192, 104, 88], "hex": "#c06858"},
        {"hue": 440, "rgb": [208, 136, 128], "hex": "#d08880"},
        {"hue": 441, "rgb": [216, 176, 168], "hex": "#d8b0a8"},
        {"hue": 442, "rgb": [144, 80, 40], "hex": "#905028"},
        {"hue": 443, "rgb": [184, 104, 48], "hex": "#b86830"},
        {"hue": 444, "rgb": [192, 136, 88], "hex": "#c08858"},
        {"hue": 445, "rgb": [208, 160, 128], "hex": "#d0a080"},
        {"hue": 446, "rgb": [216, 192, 168], "hex": "#d8c0a8"},
        {"hue": 447, "rgb": [144, 112, 40], "hex": "#907028"},
        {"hue": 448, "rgb": [184, 136, 48], "hex": "#b88830"},
        {"hue": 449, "rgb": [192, 160, 88], "hex": "#c0a058"},
        {"hue": 450, "rgb": [208, 184, 128], "hex": "#d0b880"},
        {"hue": 451, "rgb": [216, 200, 168], "hex": "#d8c8a8"},
        {"hue": 452, "rgb": [144, 144, 40], "hex": "#909028"},
        {"hue": 453, "rgb": [176, 184, 48], "hex": "#b0b830"},
        {"hue": 454, "rgb": [192, 192, 88], "hex": "#c0c058"},
        {"hue": 455, "rgb": [208, 208, 128], "hex": "#d0d080"},
        {"hue": 456, "rgb": [216, 216, 168], "hex": "#d8d8a8"},
        {"hue": 457, "rgb": [112, 144, 40], "hex": "#709028"},
        {"hue": 458, "rgb": [136, 184, 48], "hex": "#88b830"},
        {"hue": 459, "rgb": [160, 192, 88], "hex": "#a0c058"},
        {"hue": 460, "rgb": [184, 208, 128], "hex": "#b8d080"},
        {"hue": 461, "rgb": [200, 216, 168], "hex": "#c8d8a8"},
        {"hue": 462, "rgb": [80, 144, 40], "hex": "#509028"},
        {"hue": 463, "rgb": [104, 184, 48], "hex": "#68b830"},
        {"hue": 464, "rgb": [136, 192, 88], "hex": "#88c058"},
        {"hue": 465, "rgb": [160, 208, 128], "hex": "#a0d080"},
        {"hue": 466, "rgb": [192, 216, 168], "hex": "#c0d8a8"},
        {"hue": 467, "rgb": [48, 144, 40], "hex": "#309028"},
        {"hue": 468, "rgb": [64, 184, 48], "hex": "#40b830"},
        {"hue": 469, "rgb": [104, 192, 88], "hex": "#68c058"},
        {"hue": 470, "rgb": [136, 208, 128], "hex": "#88d080"},
        {"hue": 471, "rgb": [176, 216, 168], "hex": "#b0d8a8"},
        {"hue": 472, "rgb": [40, 144, 64], "hex": "#289040"},
        {"hue": 473, "rgb": [48, 184, 80], "hex": "#30b850"},
        {"hue": 474, "rgb": [88, 192, 112], "hex": "#58c070"},
        {"hue": 475, "rgb": [128, 208, 144], "hex": "#80d090"},
        {"hue": 476, "rgb": [168, 216, 176], "hex": "#a8d8b0"},
        {"hue": 477, "rgb": [40, 144, 88], "hex": "#289058"},
        {"hue": 478, "rgb": [48, 184, 120], "hex": "#30b878"},
        {"hue": 479, "rgb": [88, 192, 144], "hex": "#58c090"},
        {"hue": 480, "rgb": [128, 208, 168], "hex": "#80d0a8"},
        {"hue": 481, "rgb": [168, 216, 192], "hex": "#a8d8c0"},
        {"hue": 482, "rgb": [40, 144, 120], "hex": "#289078"},
        {"hue": 483, "rgb": [48, 184, 152], "hex": "#30b898"},
        {"hue": 484, "rgb": [88, 192, 168], "hex": "#58c0a8"},
        {"hue": 485, "rgb": [128, 208, 192], "hex": "#80d0c0"},
        {"hue": 486, "rgb": [168, 216, 208], "hex": "#a8d8d0"},
        {"hue": 487, "rgb": [40, 128, 144], "hex": "#288090"},
        {"hue": 488, "rgb": [48, 168, 184], "hex": "#30a8b8"},
        {"hue": 489, "rgb": [88, 184, 192], "hex": "#58b8c0"},
        {"hue": 490, "rgb": [128, 200, 208], "hex": "#80c8d0"},
        {"hue": 491, "rgb": [168, 216, 216], "hex": "#a8d8d8"},
        {"hue": 492, "rgb": [40, 96, 144], "hex": "#286090"},
        {"hue": 493, "rgb": [48, 128, 184], "hex": "#3080b8"},
        {"hue": 494, "rgb": [88, 152, 192], "hex": "#5898c0"},
        {"hue": 495, "rgb": [128, 176, 208], "hex": "#80b0d0"},
        {"hue": 496, "rgb": [168, 200, 216], "hex": "#a8c8d8"},
        {"hue": 497, "rgb": [40, 72, 144], "hex": "#284890"},
        {"hue": 498, "rgb": [48, 96, 184], "hex": "#3060b8"},
        {"hue": 499, "rgb": [88, 120, 192], "hex": "#5878c0"},
        {"hue": 500, "rgb": [128, 152, 208], "hex": "#8098d0"},
        {"hue": 501, "rgb": [168, 184, 216], "hex": "#a8b8d8"},
        {"hue": 502, "rgb": [48, 48, 128], "hex": "#303080"},
        {"hue": 503, "rgb": [64, 64, 168], "hex": "#4040a8"},
        {"hue": 504, "rgb": [104, 104, 184], "hex": "#6868b8"},
        {"hue": 505, "rgb": [136, 136, 200], "hex": "#8888c8"},
        {"hue": 506, "rgb": [176, 176, 216], "hex": "#b0b0d8"},
        {"hue": 507, "rgb": [72, 48, 128], "hex": "#483080"},
        {"hue": 508, "rgb": [96, 64, 168], "hex": "#6040a8"},
        {"hue": 509, "rgb": [128, 104, 184], "hex": "#8068b8"},
        {"hue": 510, "rgb": [152, 136, 200], "hex": "#9888c8"},
        {"hue": 511, "rgb": [184, 176, 216], "hex": "#b8b0d8"},
        {"hue": 512, "rgb": [96, 48, 128], "hex": "#603080"},
        {"hue": 513, "rgb": [128, 64, 168], "hex": "#8040a8"},
        {"hue": 514, "rgb": [152, 104, 184], "hex": "#9868b8"},
        {"hue": 515, "rgb": [176, 136, 200], "hex": "#b088c8"},
        {"hue": 516, "rgb": [200, 176, 216], "hex": "#c8b0d8"},
        {"hue": 517, "rgb": [120, 48, 128], "hex": "#783080"},
        {"hue": 518, "rgb": [152, 64, 168], "hex": "#9840a8"},
        {"hue": 519, "rgb": [176, 104, 184], "hex": "#b068b8"},
        {"hue": 520, "rgb": [192, 136, 200], "hex": "#c088c8"},
        {"hue": 521, "rgb": [208, 176, 216], "hex": "#d0b0d8"},
        {"hue": 522, "rgb": [128, 48, 112], "hex": "#803070"},
        {"hue": 523, "rgb": [168, 64, 144], "hex": "#a84090"},
        {"hue": 524, "rgb": [184, 104, 168], "hex": "#b868a8"},
        {"hue": 525, "rgb": [200, 136, 184], "hex": "#c888b8"},
        {"hue": 526, "rgb": [216, 176, 208], "hex": "#d8b0d0"},
        {"hue": 527, "rgb": [128, 48, 88], "hex": "#803058"},
        {"hue": 528, "rgb": [168, 64, 112], "hex": "#a84070"},
        {"hue": 529, "rgb": [184, 104, 144], "hex": "#b86890"},
        {"hue": 530, "rgb": [200, 136, 168], "hex": "#c888a8"},
        {"hue": 531, "rgb": [216, 176, 192], "hex": "#d8b0c0"},
        {"hue": 532, "rgb": [128, 48, 64], "hex": "#803040"},
        {"hue": 533, "rgb": [168, 64, 88], "hex": "#a84058"},
        {"hue": 534, "rgb": [184, 104, 120], "hex": "#b86878"},
        {"hue": 535, "rgb": [200, 136, 152], "hex": "#c88898"},
        {"hue": 536, "rgb": [216, 176, 184], "hex": "#d8b0b8"},
        {"hue": 537, "rgb": [128, 56, 48], "hex": "#803830"},
        {"hue": 538, "rgb": [168, 80, 64], "hex": "#a85040"},
        {"hue": 539, "rgb": [184, 112, 104], "hex": "#b87068"},
        {"hue": 540, "rgb": [200, 144, 136], "hex": "#c89088"},
        {"hue": 541, "rgb": [216, 176, 176], "hex": "#d8b0b0"},
        {"hue": 542, "rgb": [128, 80, 48], "hex": "#805030"},
        {"hue": 543, "rgb": [168, 104, 64], "hex": "#a86840"},
        {"hue": 544, "rgb": [184, 136, 104], "hex": "#b88868"},
        {"hue": 545, "rgb": [200, 160, 136], "hex": "#c8a088"},
        {"hue": 546, "rgb": [216, 192, 176], "hex": "#d8c0b0"},
        {"hue": 547, "rgb": [128, 104, 48], "hex": "#806830"},
        {"hue": 548, "rgb": [168, 136, 64], "hex": "#a88840"},
        {"hue": 549, "rgb": [184, 160, 104], "hex": "#b8a068"},
        {"hue": 550, "rgb": [200, 176, 136], "hex": "#c8b088"},
        {"hue": 551, "rgb": [216, 200, 176], "hex": "#d8c8b0"},
        {"hue": 552, "rgb": [128, 128, 48], "hex": "#808030"},
        {"hue": 553, "rgb": [168, 168, 64], "hex": "#a8a840"},
        {"hue": 554, "rgb": [184, 184, 104], "hex": "#b8b868"},
        {"hue": 555, "rgb": [200, 200, 136], "hex": "#c8c888"},
        {"hue": 556, "rgb": [216, 216, 176], "hex": "#d8d8b0"},
        {"hue": 557, "rgb": [104, 128, 48], "hex": "#688030"},
        {"hue": 558, "rgb": [136, 168, 64], "hex": "#88a840"},
        {"hue": 559, "rgb": [160, 184, 104], "hex": "#a0b868"},
        {"hue": 560, "rgb": [176, 200, 136], "hex": "#b0c888"},
        {"hue": 561, "rgb": [200, 216, 176], "hex": "#c8d8b0"},
        {"hue": 562, "rgb": [80, 128, 48], "hex": "#508030"},
        {"hue": 563, "rgb": [104, 168, 64], "hex": "#68a840"},
        {"hue": 564, "rgb": [136, 184, 104], "hex": "#88b868"},
        {"hue": 565, "rgb": [160, 200, 136], "hex": "#a0c888"},
        {"hue": 566, "rgb": [192, 216, 176], "hex": "#c0d8b0"},
        {"hue": 567, "rgb": [56, 128, 48], "hex": "#388030"},
        {"hue": 568, "rgb": [80, 168, 64], "hex": "#50a840"},
        {"hue": 569, "rgb": [112, 184, 104], "hex": "#70b868"},
        {"hue": 570, "rgb": [144, 200, 136], "hex": "#90c888"},
        {"hue": 571, "rgb": [176, 216, 176], "hex": "#b0d8b0"},
        {"hue": 572, "rgb": [48, 128, 64], "hex": "#308040"},
        {"hue": 573, "rgb": [64, 168, 88], "hex": "#40a858"},
        {"hue": 574, "rgb": [104, 184, 120], "hex": "#68b878"},
        {"hue": 575, "rgb": [136, 200, 152], "hex": "#88c898"},
        {"hue": 576, "rgb": [176, 216, 184], "hex": "#b0d8b8"},
        {"hue": 577, "rgb": [48, 128, 88], "hex": "#308058"},
        {"hue": 578, "rgb": [64, 168, 120], "hex": "#40a878"},
        {"hue": 579, "rgb": [104, 184, 144], "hex": "#68b890"},
        {"hue": 580, "rgb": [136, 200, 168], "hex": "#88c8a8"},
        {"hue": 581, "rgb": [176, 216, 192], "hex": "#b0d8c0"},
        {"hue": 582, "rgb": [48, 128, 112], "hex": "#308070"},
        {"hue": 583, "rgb": [64, 168, 144], "hex": "#40a890"},
        {"hue": 584, "rgb": [104, 184, 168], "hex": "#68b8a8"},
        {"hue": 585, "rgb": [136, 200, 184], "hex": "#88c8b8"},
        {"hue": 586, "rgb": [176, 216, 208], "hex": "#b0d8d0"},
        {"hue": 587, "rgb": [48, 120, 128], "hex": "#307880"},
        {"hue": 588, "rgb": [64, 152, 168], "hex": "#4098a8"},
        {"hue": 589, "rgb": [104, 176, 184], "hex": "#68b0b8"},
        {"hue": 590, "rgb": [136, 192, 200], "hex": "#88c0c8"},
        {"hue": 591, "rgb": [176, 208, 216], "hex": "#b0d0d8"},
        {"hue": 592, "rgb": [48, 96, 128], "hex": "#306080"},
        {"hue": 593, "rgb": [64, 128, 168], "hex": "#4080a8"},
        {"hue": 594, "rgb": [104, 152, 184], "hex": "#6898b8"},
        {"hue": 595, "rgb": [136, 176, 200], "hex": "#88b0c8"},
        {"hue": 596, "rgb": [176, 200, 216], "hex": "#b0c8d8"},
        {"hue": 597, "rgb": [48, 72, 128], "hex": "#304880"},
        {"hue": 598, "rgb": [64, 96, 168], "hex": "#4060a8"},
        {"hue": 599, "rgb": [104, 128, 184], "hex": "#6880b8"},
        {"hue": 600, "rgb": [136, 152, 200], "hex": "#8898c8"},
        {"hue": 601, "rgb": [176, 184, 216], "hex": "#b0b8d8"},
        {"hue": 602, "rgb": [56, 56, 120], "hex": "#383878"},
        {"hue": 603, "rgb": [80, 80, 152], "hex": "#505098"},
        {"hue": 604, "rgb": [112, 112, 176], "hex": "#7070b0"},
        {"hue": 605, "rgb": [144, 144, 192], "hex": "#9090c0"},
        {"hue": 606, "rgb": [176, 176, 208], "hex": "#b0b0d0"},
        {"hue": 607, "rgb": [80, 56, 120], "hex": "#503878"},
        {"hue": 608, "rgb": [104, 80, 152], "hex": "#685098"},
        {"hue": 609, "rgb": [128, 112, 176], "hex": "#8070b0"},
        {"hue": 610, "rgb": [160, 144, 192], "hex": "#a090c0"},
        {"hue": 611, "rgb": [184, 176, 208], "hex": "#b8b0d0"},
        {"hue": 612, "rgb": [96, 56, 120], "hex": "#603878"},
        {"hue": 613, "rgb": [120, 80, 152], "hex": "#785098"},
        {"hue": 614, "rgb": [144, 112, 176], "hex": "#9070b0"},
        {"hue": 615, "rgb": [168, 144, 192], "hex": "#a890c0"},
        {"hue": 616, "rgb": [192, 176, 208], "hex": "#c0b0d0"},
        {"hue": 617, "rgb": [112, 56, 120], "hex": "#703878"},
        {"hue": 618, "rgb": [144, 80, 152], "hex": "#905098"},
        {"hue": 619, "rgb": [168, 112, 176], "hex": "#a870b0"},
        {"hue": 620, "rgb": [184, 144, 192], "hex": "#b890c0"},
        {"hue": 621, "rgb": [208, 176, 208], "hex": "#d0b0d0"},
        {"hue": 622, "rgb": [120, 56, 104], "hex": "#783868"},
        {"hue": 623, "rgb": [152, 80, 136], "hex": "#985088"},
        {"hue": 624, "rgb": [176, 112, 160], "hex": "#b070a0"},
        {"hue": 625, "rgb": [192, 144, 184], "hex": "#c090b8"},
        {"hue": 626, "rgb": [208, 176, 200], "hex": "#d0b0c8"},
        {"hue": 627, "rgb": [120, 56, 88], "hex": "#783858"},
        {"hue": 628, "rgb": [152, 80, 112], "hex": "#985070"},
        {"hue": 629, "rgb": [176, 112, 144], "hex": "#b07090"},
        {"hue": 630, "rgb": [192, 144, 168], "hex": "#c090a8"},
        {"hue": 631, "rgb": [208, 176, 192], "hex": "#d0b0c0"},
        {"hue": 632, "rgb": [120, 56, 72], "hex": "#783848"},
        {"hue": 633, "rgb": [152, 80, 96], "hex": "#985060"},
        {"hue": 634, "rgb": [176, 112, 128], "hex": "#b07080"},
        {"hue": 635, "rgb": [192, 144, 152], "hex": "#c09098"},
        {"hue": 636, "rgb": [208, 176, 184], "hex": "#d0b0b8"},
        {"hue": 637, "rgb": [120, 64, 56], "hex": "#784038"},
        {"hue": 638, "rgb": [152, 88, 80], "hex": "#985850"},
        {"hue": 639, "rgb": [176, 120, 112], "hex": "#b07870"},
        {"hue": 640, "rgb": [192, 152, 144], "hex": "#c09890"},
        {"hue": 641, "rgb": [208, 184, 176], "hex": "#d0b8b0"},
        {"hue": 642, "rgb": [120, 88, 56], "hex": "#785838"},
        {"hue": 643, "rgb": [152, 112, 80], "hex": "#987050"},
        {"hue": 644, "rgb": [176, 136, 112], "hex": "#b08870"},
        {"hue": 645, "rgb": [192, 160, 144], "hex": "#c0a090"},
        {"hue": 646, "rgb": [208, 192, 176], "hex": "#d0c0b0"},
        {"hue": 647, "rgb": [120, 104, 56], "hex": "#786838"},
        {"hue": 648, "rgb": [152, 128, 80], "hex": "#988050"},
        {"hue": 649, "rgb": [176, 152, 112], "hex": "#b09870"},
        {"hue": 650, "rgb": [192, 176, 144], "hex": "#c0b090"},
        {"hue": 651, "rgb": [208, 200, 176], "hex": "#d0c8b0"},
        {"hue": 652, "rgb": [120, 120, 56], "hex": "#787838"},
        {"hue": 653, "rgb": [152, 152, 80], "hex": "#989850"},
        {"hue": 654, "rgb": [176, 176, 112], "hex": "#b0b070"},
        {"hue": 655, "rgb": [192, 192, 144], "hex": "#c0c090"},
        {"hue": 656, "rgb": [208, 208, 176], "hex": "#d0d0b0"},
        {"hue": 657, "rgb": [104, 120, 56], "hex": "#687838"},
        {"hue": 658, "rgb": [128, 152, 80], "hex": "#809850"},
        {"hue": 659, "rgb": [152, 176, 112], "hex": "#98b070"},
        {"hue": 660, "rgb": [176, 192, 144], "hex": "#b0c090"},
        {"hue": 661, "rgb": [200, 208, 176], "hex": "#c8d0b0"},
        {"hue": 662, "rgb": [88, 120, 56], "hex": "#587838"},
        {"hue": 663, "rgb": [112, 152, 80], "hex": "#709850"},
        {"hue": 664, "rgb": [136, 176, 112], "hex": "#88b070"},
        {"hue": 665, "rgb": [160, 192, 144], "hex": "#a0c090"},
        {"hue": 666, "rgb": [192, 208, 176], "hex": "#c0d0b0"},
        {"hue": 667, "rgb": [64, 120, 56], "hex": "#407838"},
        {"hue": 668, "rgb": [88, 152, 80], "hex": "#589850"},
        {"hue": 669, "rgb": [120, 176, 112], "hex": "#78b070"},
        {"hue": 670, "rgb": [152, 192, 144], "hex": "#98c090"},
        {"hue": 671, "rgb": [184, 208, 176], "hex": "#b8d0b0"},
        {"hue": 672, "rgb": [56, 120, 72], "hex": "#387848"},
        {"hue": 673, "rgb": [80, 152, 96], "hex": "#509860"},
        {"hue": 674, "rgb": [112, 176, 128], "hex": "#70b080"},
        {"hue": 675, "rgb": [144, 192, 152], "hex": "#90c098"},
        {"hue": 676, "rgb": [176, 208, 184], "hex": "#b0d0b8"},
        {"hue": 677, "rgb": [56, 120, 88], "hex": "#387858"},
        {"hue": 678, "rgb": [80, 152, 120], "hex": "#509878"},
        {"hue": 679, "rgb": [112, 176, 144], "hex": "#70b090"},
        {"hue": 680, "rgb": [144, 192, 168], "hex": "#90c0a8"},
        {"hue": 681, "rgb": [176, 208, 192], "hex": "#b0d0c0"},
        {"hue": 682, "rgb": [56, 120, 104], "hex": "#387868"},
        {"hue": 683, "rgb": [80, 152, 136], "hex": "#509888"},
        {"hue": 684, "rgb": [112, 176, 160], "hex": "#70b0a0"},
        {"hue": 685, "rgb": [144, 192, 184], "hex": "#90c0b8"},
        {"hue": 686, "rgb": [176, 208, 200], "hex": "#b0d0c8"},
        {"hue": 687, "rgb": [56, 112, 120], "hex": "#387078"},
        {"hue": 688, "rgb": [80, 144, 152], "hex": "#509098"},
        {"hue": 689, "rgb": [112, 168, 176], "hex": "#70a8b0"},
        {"hue": 690, "rgb": [144, 184, 192], "hex": "#90b8c0"},
        {"hue": 691, "rgb": [176, 208, 208], "hex": "#b0d0d0"},
        {"hue": 692, "rgb": [56, 96, 120], "hex": "#386078"},
        {"hue": 693, "rgb": [80, 120, 152], "hex": "#507898"},
        {"hue": 694, "rgb": [112, 144, 176], "hex": "#7090b0"},
        {"hue": 695, "rgb": [144, 168, 192], "hex": "#90a8c0"},
        {"hue": 696, "rgb": [176, 192, 208], "hex": "#b0c0d0"},
        {"hue": 697, "rgb": [56, 80, 120], "hex": "#385078"},
        {"hue": 698, "rgb": [80, 104, 152], "hex": "#506898"},
        {"hue": 699, "rgb": [112, 128, 176], "hex": "#7080b0"},
        {"hue": 700, "rgb": [144, 160, 192], "hex": "#90a0c0"},
        {"hue": 701, "rgb": [176, 184, 208], "hex": "#b0b8d0"},
        {"hue": 702, "rgb": [72, 72, 112], "hex": "#484870"},
        {"hue": 703, "rgb": [88, 88, 144], "hex": "#585890"},
        {"hue": 704, "rgb": [120, 120, 160], "hex": "#7878a0"},
        {"hue": 705, "rgb": [152, 152, 184], "hex": "#9898b8"},
        {"hue": 706, "rgb": [184, 184, 200], "hex": "#b8b8c8"},
        {"hue": 707, "rgb": [80, 72, 112], "hex": "#504870"},
        {"hue": 708, "rgb": [104, 88, 144], "hex": "#685890"},
        {"hue": 709, "rgb": [136, 120, 160], "hex": "#8878a0"},
        {"hue": 710, "rgb": [160, 152, 184], "hex": "#a098b8"},
        {"hue": 711, "rgb": [192, 184, 200], "hex": "#c0b8c8"},
        {"hue": 712, "rgb": [96, 72, 112], "hex": "#604870"},
        {"hue": 713, "rgb": [120, 88, 144], "hex": "#785890"},
        {"hue": 714, "rgb": [144, 120, 160], "hex": "#9078a0"},
        {"hue": 715, "rgb": [168, 152, 184], "hex": "#a898b8"},
        {"hue": 717, "rgb": [104, 72, 112], "hex": "#684870"},
        {"hue": 718, "rgb": [136, 88, 144], "hex": "#885890"},
        {"hue": 719, "rgb": [160, 120, 160], "hex": "#a078a0"},
        {"hue": 720, "rgb": [176, 152, 184], "hex": "#b098b8"},
        {"hue": 721, "rgb": [200, 184, 200], "hex": "#c8b8c8"},
        {"hue": 722, "rgb": [112, 72, 104], "hex": "#704868"},
        {"hue": 723, "rgb": [144, 88, 128], "hex": "#905880"},
        {"hue": 724, "rgb": [160, 120, 152], "hex": "#a07898"},
        {"hue": 725, "rgb": [184, 152, 176], "hex": "#b898b0"},
        {"hue": 727, "rgb": [112, 72, 88], "hex": "#704858"},
        {"hue": 728, "rgb": [144, 88, 112], "hex": "#905870"},
        {"hue": 729, "rgb": [160, 120, 144], "hex": "#a07890"},
        {"hue": 730, "rgb": [184, 152, 168], "hex": "#b898a8"},
        {"hue": 731, "rgb": [200, 184, 192], "hex": "#c8b8c0"},
        {"hue": 732, "rgb": [112, 72, 80], "hex": "#704850"},
        {"hue": 733, "rgb": [144, 88, 104], "hex": "#905868"},
        {"hue": 734, "rgb": [160, 120, 128], "hex": "#a07880"},
        {"hue": 735, "rgb": [184, 152, 160], "hex": "#b898a0"},
        {"hue": 736, "rgb": [200, 184, 184], "hex": "#c8b8b8"},
        {"hue": 737, "rgb": [112, 72, 72], "hex": "#704848"},
        {"hue": 738, "rgb": [144, 96, 88], "hex": "#906058"},
        {"hue": 739, "rgb": [160, 128, 120], "hex": "#a08078"},
        {"hue": 740, "rgb": [184, 152, 152], "hex": "#b89898"},
        {"hue": 742, "rgb": [112, 88, 72], "hex": "#705848"},
        {"hue": 743, "rgb": [144, 112, 88], "hex": "#907058"},
        {"hue": 744, "rgb": [160, 136, 120], "hex": "#a08878"},
        {"hue": 745, "rgb": [184, 168, 152], "hex": "#b8a898"},
        {"hue": 746, "rgb": [200, 192, 184], "hex": "#c8c0b8"},
        {"hue": 747, "rgb": [112, 96, 72], "hex": "#706048"},
        {"hue": 748, "rgb": [144, 128, 88], "hex": "#908058"},
        {"hue": 749, "rgb": [160, 152, 120], "hex": "#a09878"},
        {"hue": 750, "rgb": [184, 176, 152], "hex": "#b8b098"},
        {"hue": 751, "rgb": [200, 200, 184], "hex": "#c8c8b8"},
        {"hue": 752, "rgb": [112, 112, 72], "hex": "#707048"},
        {"hue": 753, "rgb": [144, 144, 88], "hex": "#909058"},
        {"hue": 754, "rgb": [160, 160, 120], "hex": "#a0a078"},
        {"hue": 755, "rgb": [184, 184, 152], "hex": "#b8b898"},
        {"hue": 757, "rgb": [96, 112, 72], "hex": "#607048"},
        {"hue": 758, "rgb": [128, 144, 88], "hex": "#809058"},
        {"hue": 759, "rgb": [152, 160, 120], "hex": "#98a078"},
        {"hue": 760, "rgb": [176, 184, 152], "hex": "#b0b898"},
        {"hue": 762, "rgb": [88, 112, 72], "hex": "#587048"},
        {"hue": 763, "rgb": [112, 144, 88], "hex": "#709058"},
        {"hue": 764, "rgb": [136, 160, 120], "hex": "#88a078"},
        {"hue": 765, "rgb": [168, 184, 152], "hex": "#a8b898"},
        {"hue": 766, "rgb": [192, 200, 184], "hex": "#c0c8b8"},
        {"hue": 767, "rgb": [72, 112, 72], "hex": "#487048"},
        {"hue": 768, "rgb": [96, 144, 88], "hex": "#609058"},
        {"hue": 769, "rgb": [128, 160, 120], "hex": "#80a078"},
        {"hue": 770, "rgb": [152, 184, 152], "hex": "#98b898"},
        {"hue": 771, "rgb": [184, 200, 184], "hex": "#b8c8b8"},
        {"hue": 772, "rgb": [72, 112, 80], "hex": "#487050"},
        {"hue": 773, "rgb": [88, 144, 104], "hex": "#589068"},
        {"hue": 774, "rgb": [120, 160, 128], "hex": "#78a080"},
        {"hue": 775, "rgb": [152, 184, 160], "hex": "#98b8a0"},
        {"hue": 777, "rgb": [72, 112, 88], "hex": "#487058"},
        {"hue": 778, "rgb": [88, 144, 120], "hex": "#589078"},
        {"hue": 779, "rgb": [120, 160, 144], "hex": "#78a090"},
        {"hue": 780, "rgb": [152, 184, 168], "hex": "#98b8a8"},
        {"hue": 781, "rgb": [184, 200, 192], "hex": "#b8c8c0"},
        {"hue": 782, "rgb": [72, 112, 104], "hex": "#487068"},
        {"hue": 783, "rgb": [88, 144, 128], "hex": "#589080"},
        {"hue": 784, "rgb": [120, 160, 152], "hex": "#78a098"},
        {"hue": 785, "rgb": [152, 184, 176], "hex": "#98b8b0"},
        {"hue": 786, "rgb": [184, 200, 200], "hex": "#b8c8c8"},
        {"hue": 787, "rgb": [72, 104, 112], "hex": "#486870"},
        {"hue": 788, "rgb": [88, 136, 144], "hex": "#588890"},
        {"hue": 789, "rgb": [120, 160, 160], "hex": "#78a0a0"},
        {"hue": 790, "rgb": [152, 176, 184], "hex": "#98b0b8"},
        {"hue": 792, "rgb": [72, 96, 112], "hex": "#486070"},
        {"hue": 793, "rgb": [88, 120, 144], "hex": "#587890"},
        {"hue": 794, "rgb": [120, 144, 160], "hex": "#7890a0"},
        {"hue": 795, "rgb": [152, 168, 184], "hex": "#98a8b8"},
        {"hue": 796, "rgb": [184, 192, 200], "hex": "#b8c0c8"},
        {"hue": 797, "rgb": [72, 80, 112], "hex": "#485070"},
        {"hue": 798, "rgb": [88, 104, 144], "hex": "#586890"},
        {"hue": 799, "rgb": [120, 136, 160], "hex": "#7888a0"},
        {"hue": 800, "rgb": [152, 160, 184], "hex": "#98a0b8"},
        {"hue": 802, "rgb": [80, 80, 104], "hex": "#505068"},
        {"hue": 803, "rgb": [104, 104, 128], "hex": "#686880"},
        {"hue": 804, "rgb": [128, 128, 152], "hex": "#808098"},
        {"hue": 805, "rgb": [160, 160, 176], "hex": "#a0a0b0"},
        {"hue": 807, "rgb": [88, 80, 104], "hex": "#585068"},
        {"hue": 808, "rgb": [112, 104, 128], "hex": "#706880"},
        {"hue": 809, "rgb": [136, 128, 152], "hex": "#888098"},
        {"hue": 810, "rgb": [168, 160, 176], "hex": "#a8a0b0"},
        {"hue": 812, "rgb": [96, 80, 104], "hex": "#605068"},
        {"hue": 813, "rgb": [120, 104, 128], "hex": "#786880"},
        {"hue": 814, "rgb": [144, 128, 152], "hex": "#908098"},
        {"hue": 818, "rgb": [128, 104, 128], "hex": "#806880"},
        {"hue": 819, "rgb": [152, 128, 152], "hex": "#988098"},
        {"hue": 820, "rgb": [176, 160, 176], "hex": "#b0a0b0"},
        {"hue": 822, "rgb": [104, 80, 96], "hex": "#685060"},
        {"hue": 823, "rgb": [128, 104, 120], "hex": "#806878"},
        {"hue": 824, "rgb": [152, 128, 144], "hex": "#988090"},
        {"hue": 825, "rgb": [176, 160, 168], "hex": "#b0a0a8"},
        {"hue": 827, "rgb": [104, 80, 88], "hex": "#685058"},
        {"hue": 828, "rgb": [128, 104, 112], "hex": "#806870"},
        {"hue": 834, "rgb": [152, 128, 136], "hex": "#988088"},
        {"hue": 835, "rgb": [176, 160, 160], "hex": "#b0a0a0"},
        {"hue": 837, "rgb": [104, 80, 80], "hex": "#685050"},
        {"hue": 838, "rgb": [128, 104, 104], "hex": "#806868"},
        {"hue": 839, "rgb": [152, 136, 128], "hex": "#988880"},
        {"hue": 842, "rgb": [104, 88, 80], "hex": "#685850"},
        {"hue": 843, "rgb": [128, 112, 104], "hex": "#807068"},
        {"hue": 845, "rgb": [176, 168, 160], "hex": "#b0a8a0"},
        {"hue": 847, "rgb": [104, 96, 80], "hex": "#686050"},
        {"hue": 848, "rgb": [128, 120, 104], "hex": "#807868"},
        {"hue": 849, "rgb": [152, 144, 128], "hex": "#989080"},
        {"hue": 852, "rgb": [104, 104, 80], "hex": "#686850"},
        {"hue": 853, "rgb": [128, 128, 104], "hex": "#808068"},
        {"hue": 854, "rgb": [152, 152, 128], "hex": "#989880"},
        {"hue": 855, "rgb": [176, 176, 160], "hex": "#b0b0a0"},
        {"hue": 857, "rgb": [96, 104, 80], "hex": "#606850"},
        {"hue": 858, "rgb": [120, 128, 104], "hex": "#788068"},
        {"hue": 859, "rgb": [144, 152, 128], "hex": "#909880"},
        {"hue": 860, "rgb": [168, 176, 160], "hex": "#a8b0a0"},
        {"hue": 862, "rgb": [88, 104, 80], "hex": "#586850"},
        {"hue": 863, "rgb": [112, 128, 104], "hex": "#708068"},
        {"hue": 864, "rgb": [136, 152, 128], "hex": "#889880"},
        {"hue": 867, "rgb": [80, 104, 80], "hex": "#506850"},
        {"hue": 868, "rgb": [104, 128, 104], "hex": "#688068"},
        {"hue": 870, "rgb": [160, 176, 160], "hex": "#a0b0a0"},
        {"hue": 872, "rgb": [80, 104, 88], "hex": "#506858"},
        {"hue": 873, "rgb": [104, 128, 112], "hex": "#688070"},
        {"hue": 874, "rgb": [128, 152, 136], "hex": "#809888"},
        {"hue": 878, "rgb": [104, 128, 120], "hex": "#688078"},
        {"hue": 879, "rgb": [128, 152, 144], "hex": "#809890"},
        {"hue": 880, "rgb": [160, 176, 168], "hex": "#a0b0a8"},
        {"hue": 882, "rgb": [80, 104, 96], "hex": "#506860"},
        {"hue": 887, "rgb": [80, 96, 104], "hex": "#506068"},
        {"hue": 888, "rgb": [104, 128, 128], "hex": "#688080"},
        {"hue": 889, "rgb": [128, 152, 152], "hex": "#809898"},
        {"hue": 890, "rgb": [160, 176, 176], "hex": "#a0b0b0"},
        {"hue": 893, "rgb": [104, 120, 128], "hex": "#687880"},
        {"hue": 894, "rgb": [128, 144, 152], "hex": "#809098"},
        {"hue": 895, "rgb": [160, 168, 176], "hex": "#a0a8b0"},
        {"hue": 897, "rgb": [80, 88, 104], "hex": "#505868"},
        {"hue": 898, "rgb": [104, 112, 128], "hex": "#687080"},
        {"hue": 899, "rgb": [128, 136, 152], "hex": "#808898"},
        {"hue": 902, "rgb": [88, 88, 88], "hex": "#585858"},
        {"hue": 903, "rgb": [120, 120, 120], "hex": "#787878"},
        {"hue": 904, "rgb": [144, 144, 144], "hex": "#909090"},
        {"hue": 905, "rgb": [168, 168, 168], "hex": "#a8a8a8"},
        {"hue": 906, "rgb": [192, 192, 192], "hex": "#c0c0c0"},
        {"hue": 1002, "rgb": [224, 176, 160], "hex": "#e0b0a0"},
        {"hue": 1003, "rgb": [208, 160, 144], "hex": "#d0a090"},
        {"hue": 1004, "rgb": [192, 144, 120], "hex": "#c09078"},
        {"hue": 1005, "rgb": [184, 128, 112], "hex": "#b88070"},
        {"hue": 1006, "rgb": [168, 120, 96], "hex": "#a87860"},
        {"hue": 1007, "rgb": [152, 104, 80], "hex": "#986850"},
        {"hue": 1008, "rgb": [136, 80, 64], "hex": "#885040"},
        {"hue": 1012, "rgb": [184, 136, 112], "hex": "#b88870"},
        {"hue": 1013, "rgb": [168, 120, 104], "hex": "#a87868"},
        {"hue": 1014, "rgb": [152, 104, 88], "hex": "#986858"},
        {"hue": 1015, "rgb": [128, 80, 64], "hex": "#805040"},
        {"hue": 1018, "rgb": [184, 144, 128], "hex": "#b89080"},
        {"hue": 1019, "rgb": [176, 128, 120], "hex": "#b08078"},
        {"hue": 1021, "rgb": [144, 104, 88], "hex": "#906858"},
        {"hue": 1023, "rgb": [216, 184, 168], "hex": "#d8b8a8"},
        {"hue": 1024, "rgb": [200, 160, 144], "hex": "#c8a090"},
        {"hue": 1025, "rgb": [176, 144, 128], "hex": "#b09080"},
        {"hue": 1026, "rgb": [168, 136, 120], "hex": "#a88878"},
        {"hue": 1027, "rgb": [160, 120, 104], "hex": "#a07868"},
        {"hue": 1028, "rgb": [136, 104, 88], "hex": "#886858"},
        {"hue": 1029, "rgb": [120, 80, 72], "hex": "#785048"},
        {"hue": 1030, "rgb": [216, 184, 160], "hex": "#d8b8a0"},
        {"hue": 1031, "rgb": [200, 168, 144], "hex": "#c8a890"},
        {"hue": 1032, "rgb": [184, 144, 120], "hex": "#b89078"},
        {"hue": 1033, "rgb": [168, 136, 112], "hex": "#a88870"},
        {"hue": 1034, "rgb": [160, 128, 96], "hex": "#a08060"},
        {"hue": 1035, "rgb": [136, 104, 80], "hex": "#886850"},
        {"hue": 1036, "rgb": [120, 88, 64], "hex": "#785840"},
        {"hue": 1039, "rgb": [176, 144, 120], "hex": "#b09078"},
        {"hue": 1045, "rgb": [208, 184, 152], "hex": "#d0b898"},
        {"hue": 1046, "rgb": [192, 168, 136], "hex": "#c0a888"},
        {"hue": 1047, "rgb": [176, 152, 120], "hex": "#b09878"},
        {"hue": 1049, "rgb": [152, 128, 96], "hex": "#988060"},
        {"hue": 1050, "rgb": [128, 104, 80], "hex": "#806850"},
        {"hue": 1051, "rgb": [112, 88, 56], "hex": "#705838"},
        {"hue": 1052, "rgb": [216, 184, 136], "hex": "#d8b888"},
        {"hue": 1053, "rgb": [200, 168, 120], "hex": "#c8a878"},
        {"hue": 1054, "rgb": [184, 144, 104], "hex": "#b89068"},
        {"hue": 1055, "rgb": [176, 136, 88], "hex": "#b08858"},
        {"hue": 1056, "rgb": [168, 128, 80], "hex": "#a88050"},
        {"hue": 1057, "rgb": [144, 104, 64], "hex": "#906840"},
        {"hue": 1058, "rgb": [120, 88, 48], "hex": "#785830"},
        {"hue": 1059, "rgb": [168, 208, 40], "hex": "#a8d028"},
        {"hue": 1060, "rgb": [168, 16, 152], "hex": "#a81098"},
        {"hue": 1061, "rgb": [48, 200, 112], "hex": "#30c870"},
        {"hue": 1062, "rgb": [128, 208, 160], "hex": "#80d0a0"},
        {"hue": 1063, "rgb": [32, 208, 40], "hex": "#20d028"},
        {"hue": 1064, "rgb": [96, 240, 184], "hex": "#60f0b8"},
        {"hue": 1065, "rgb": [0, 0, 32], "hex": "#000020"},
        {"hue": 1066, "rgb": [32, 240, 208], "hex": "#20f0d0"},
        {"hue": 1067, "rgb": [8, 0, 0], "hex": "#080000"},
        {"hue": 1068, "rgb": [168, 0, 64], "hex": "#a80040"},
        {"hue": 1069, "rgb": [16, 128, 32], "hex": "#108020"},
        {"hue": 1070, "rgb": [136, 208, 40], "hex": "#88d028"},
        {"hue": 1072, "rgb": [240, 240, 240], "hex": "#f0f0f0"},
        {"hue": 1073, "rgb": [128, 80, 144], "hex": "#805090"},
        {"hue": 1074, "rgb": [0, 0, 80], "hex": "#000050"},
        {"hue": 1076, "rgb": [184, 216, 40], "hex": "#b8d828"},
        {"hue": 1078, "rgb": [152, 192, 112], "hex": "#98c070"},
        {"hue": 1079, "rgb": [168, 16, 112], "hex": "#a81070"},
        {"hue": 1080, "rgb": [152, 80, 40], "hex": "#985028"},
        {"hue": 1081, "rgb": [160, 144, 160], "hex": "#a090a0"},
        {"hue": 1082, "rgb": [128, 208, 152], "hex": "#80d098"},
        {"hue": 1083, "rgb": [104, 184, 192], "hex": "#68b8c0"},
        {"hue": 1084, "rgb": [0, 0, 72], "hex": "#000048"},
        {"hue": 1087, "rgb": [168, 16, 40], "hex": "#a81028"},
        {"hue": 1089, "rgb": [216, 216, 152], "hex": "#d8d898"},
        {"hue": 1090, "rgb": [144, 16, 24], "hex": "#901018"},
        {"hue": 1092, "rgb": [152, 208, 96], "hex": "#98d060"},
        {"hue": 1093, "rgb": [0, 0, 96], "hex": "#000060"},
        {"hue": 1095, "rgb": [0, 0, 216], "hex": "#0000d8"},
        {"hue": 1096, "rgb": [128, 80, 160], "hex": "#8050a0"},
        {"hue": 1097, "rgb": [0, 120, 112], "hex": "#007870"},
        {"hue": 1099, "rgb": [32, 240, 16], "hex": "#20f010"},
        {"hue": 1103, "rgb": [144, 144, 160], "hex": "#9090a0"},
        {"hue": 1104, "rgb": [136, 136, 152], "hex": "#888898"},
        {"hue": 1105, "rgb": [128, 128, 144], "hex": "#808090"},
        {"hue": 1106, "rgb": [112, 112, 128], "hex": "#707080"},
        {"hue": 1107, "rgb": [104, 104, 120], "hex": "#686878"},
        {"hue": 1108, "rgb": [88, 88, 104], "hex": "#585868"},
        {"hue": 1109, "rgb": [72, 72, 88], "hex": "#484858"},
        {"hue": 1111, "rgb": [184, 160, 120], "hex": "#b8a078"},
        {"hue": 1113, "rgb": [168, 136, 104], "hex": "#a88868"},
        {"hue": 1115, "rgb": [144, 120, 80], "hex": "#907850"},
        {"hue": 1116, "rgb": [136, 104, 64], "hex": "#886840"},
        {"hue": 1117, "rgb": [120, 80, 48], "hex": "#785030"},
        {"hue": 1118, "rgb": [208, 168, 88], "hex": "#d0a858"},
        {"hue": 1119, "rgb": [200, 160, 80], "hex": "#c8a050"},
        {"hue": 1120, "rgb": [192, 152, 72], "hex": "#c09848"},
        {"hue": 1121, "rgb": [184, 144, 64], "hex": "#b89040"},
        {"hue": 1122, "rgb": [168, 136, 48], "hex": "#a88830"},
        {"hue": 1123, "rgb": [160, 120, 32], "hex": "#a07820"},
        {"hue": 1124, "rgb": [152, 112, 16], "hex": "#987010"},
        {"hue": 1125, "rgb": [136, 88, 8], "hex": "#885808"},
        {"hue": 1126, "rgb": [208, 144, 0], "hex": "#d09000"},
        {"hue": 1127, "rgb": [200, 136, 0], "hex": "#c88800"},
        {"hue": 1128, "rgb": [184, 120, 0], "hex": "#b87800"},
        {"hue": 1129, "rgb": [168, 112, 0], "hex": "#a87000"},
        {"hue": 1130, "rgb": [152, 104, 0], "hex": "#986800"},
        {"hue": 1131, "rgb": [136, 96, 0], "hex": "#886000"},
        {"hue": 1132, "rgb": [120, 80, 0], "hex": "#785000"},
        {"hue": 1133, "rgb": [96, 64, 0], "hex": "#604000"},
        {"hue": 1134, "rgb": [192, 128, 80], "hex": "#c08050"},
        {"hue": 1135, "rgb": [184, 120, 72], "hex": "#b87848"},
        {"hue": 1136, "rgb": [176, 104, 64], "hex": "#b06840"},
        {"hue": 1137, "rgb": [160, 96, 56], "hex": "#a06038"},
        {"hue": 1138, "rgb": [152, 88, 48], "hex": "#985830"},
        {"hue": 1139, "rgb": [136, 72, 32], "hex": "#884820"},
        {"hue": 1140, "rgb": [128, 64, 24], "hex": "#804018"},
        {"hue": 1141, "rgb": [112, 40, 16], "hex": "#702810"},
        {"hue": 1143, "rgb": [144, 96, 72], "hex": "#906048"},
        {"hue": 1144, "rgb": [136, 88, 64], "hex": "#885840"},
        {"hue": 1145, "rgb": [128, 72, 56], "hex": "#804838"},
        {"hue": 1146, "rgb": [112, 64, 48], "hex": "#704030"},
        {"hue": 1147, "rgb": [104, 56, 40], "hex": "#683828"},
        {"hue": 1148, "rgb": [96, 48, 24], "hex": "#603018"},
        {"hue": 1149, "rgb": [72, 32, 16], "hex": "#482010"},
        {"hue": 1150, "rgb": [248, 248, 248], "hex": "#f8f8f8"},
        {"hue": 1151, "rgb": [176, 240, 240], "hex": "#b0f0f0"},
        {"hue": 1152, "rgb": [0, 0, 144], "hex": "#000090"},
        {"hue": 1154, "rgb": [216, 240, 240], "hex": "#d8f0f0"},
        {"hue": 1155, "rgb": [40, 96, 40], "hex": "#286028"},
        {"hue": 1156, "rgb": [0, 24, 104], "hex": "#001868"},
        {"hue": 1157, "rgb": [104, 0, 0], "hex": "#680000"},
        {"hue": 1158, "rgb": [144, 8, 136], "hex": "#900888"},
        {"hue": 1159, "rgb": [200, 200, 16], "hex": "#c8c810"},
        {"hue": 1160, "rgb": [0, 168, 160], "hex": "#00a8a0"},
        {"hue": 1161, "rgb": [240, 248, 0], "hex": "#f0f800"},
        {"hue": 1162, "rgb": [8, 184, 176], "hex": "#08b8b0"},
        {"hue": 1163, "rgb": [136, 48, 128], "hex": "#883080"},
        {"hue": 1164, "rgb": [80, 128, 64], "hex": "#508040"},
        {"hue": 1165, "rgb": [192, 192, 232], "hex": "#c0c0e8"},
        {"hue": 1166, "rgb": [232, 192, 192], "hex": "#e8c0c0"},
        {"hue": 1167, "rgb": [224, 240, 224], "hex": "#e0f0e0"},
        {"hue": 1168, "rgb": [224, 176, 216], "hex": "#e0b0d8"},
        {"hue": 1170, "rgb": [224, 184, 144], "hex": "#e0b890"},
        {"hue": 1171, "rgb": [88, 136, 88], "hex": "#588858"},
        {"hue": 1172, "rgb": [216, 16, 32], "hex": "#d81020"},
        {"hue": 1173, "rgb": [32, 192, 184], "hex": "#20c0b8"},
        {"hue": 1174, "rgb": [152, 88, 16], "hex": "#985810"},
        {"hue": 1175, "rgb": [56, 56, 56], "hex": "#383838"},
        {"hue": 1176, "rgb": [0, 0, 208], "hex": "#0000d0"},
        {"hue": 1177, "rgb": [64, 56, 32], "hex": "#403820"},
        {"hue": 1179, "rgb": [16, 248, 144], "hex": "#10f890"},
        {"hue": 1181, "rgb": [16, 248, 88], "hex": "#10f858"},
        {"hue": 1183, "rgb": [24, 56, 240], "hex": "#1838f0"},
        {"hue": 1190, "rgb": [88, 56, 16], "hex": "#583810"},
        {"hue": 1191, "rgb": [208, 208, 144], "hex": "#d0d090"},
        {"hue": 1192, "rgb": [176, 104, 0], "hex": "#b06800"},
        {"hue": 1193, "rgb": [16, 96, 16], "hex": "#106010"},
        {"hue": 1194, "rgb": [224, 32, 40], "hex": "#e02028"},
        {"hue": 1195, "rgb": [192, 192, 248], "hex": "#c0c0f8"},
        {"hue": 1196, "rgb": [248, 248, 0], "hex": "#f8f800"},
        {"hue": 1201, "rgb": [240, 160, 160], "hex": "#f0a0a0"},
        {"hue": 1202, "rgb": [240, 136, 144], "hex": "#f08890"},
        {"hue": 1203, "rgb": [240, 120, 128], "hex": "#f07880"},
        {"hue": 1204, "rgb": [240, 104, 112], "hex": "#f06870"},
        {"hue": 1205, "rgb": [232, 96, 104], "hex": "#e86068"},
        {"hue": 1206, "rgb": [224, 88, 96], "hex": "#e05860"},
        {"hue": 1207, "rgb": [208, 72, 80], "hex": "#d04850"},
        {"hue": 1208, "rgb": [200, 64, 72], "hex": "#c84048"},
        {"hue": 1209, "rgb": [184, 48, 56], "hex": "#b83038"},
        {"hue": 1211, "rgb": [240, 144, 144], "hex": "#f09090"},
        {"hue": 1212, "rgb": [224, 128, 128], "hex": "#e08080"},
        {"hue": 1213, "rgb": [216, 120, 120], "hex": "#d87878"},
        {"hue": 1214, "rgb": [208, 104, 104], "hex": "#d06868"},
        {"hue": 1215, "rgb": [200, 96, 96], "hex": "#c86060"},
        {"hue": 1216, "rgb": [184, 88, 88], "hex": "#b85858"},
        {"hue": 1217, "rgb": [176, 72, 72], "hex": "#b04848"},
        {"hue": 1218, "rgb": [160, 64, 64], "hex": "#a04040"},
        {"hue": 1220, "rgb": [224, 144, 160], "hex": "#e090a0"},
        {"hue": 1221, "rgb": [208, 136, 144], "hex": "#d08890"},
        {"hue": 1222, "rgb": [200, 120, 136], "hex": "#c87888"},
        {"hue": 1223, "rgb": [192, 112, 128], "hex": "#c07080"},
        {"hue": 1224, "rgb": [176, 104, 112], "hex": "#b06870"},
        {"hue": 1225, "rgb": [168, 88, 104], "hex": "#a85868"},
        {"hue": 1227, "rgb": [144, 64, 80], "hex": "#904050"},
        {"hue": 1229, "rgb": [216, 144, 176], "hex": "#d890b0"},
        {"hue": 1231, "rgb": [192, 120, 152], "hex": "#c07898"},
        {"hue": 1232, "rgb": [184, 112, 144], "hex": "#b87090"},
        {"hue": 1233, "rgb": [168, 104, 136], "hex": "#a86888"},
        {"hue": 1234, "rgb": [160, 88, 120], "hex": "#a05878"},
        {"hue": 1235, "rgb": [144, 80, 112], "hex": "#905070"},
        {"hue": 1236, "rgb": [136, 64, 96], "hex": "#884060"},
        {"hue": 1237, "rgb": [208, 168, 200], "hex": "#d0a8c8"},
        {"hue": 1238, "rgb": [200, 152, 192], "hex": "#c898c0"},
        {"hue": 1239, "rgb": [184, 144, 176], "hex": "#b890b0"},
        {"hue": 1240, "rgb": [176, 128, 168], "hex": "#b080a8"},
        {"hue": 1242, "rgb": [152, 112, 144], "hex": "#987090"},
        {"hue": 1243, "rgb": [144, 96, 136], "hex": "#906088"},
        {"hue": 1244, "rgb": [128, 88, 120], "hex": "#805878"},
        {"hue": 1245, "rgb": [120, 72, 112], "hex": "#784870"},
        {"hue": 1247, "rgb": [184, 160, 200], "hex": "#b8a0c8"},
        {"hue": 1249, "rgb": [160, 136, 176], "hex": "#a088b0"},
        {"hue": 1250, "rgb": [144, 128, 168], "hex": "#9080a8"},
        {"hue": 1251, "rgb": [136, 120, 152], "hex": "#887898"},
        {"hue": 1252, "rgb": [128, 104, 144], "hex": "#806890"},
        {"hue": 1253, "rgb": [112, 96, 128], "hex": "#706080"},
        {"hue": 1254, "rgb": [104, 80, 120], "hex": "#685078"},
        {"hue": 1255, "rgb": [160, 88, 0], "hex": "#a05800"},
        {"hue": 1256, "rgb": [200, 120, 8], "hex": "#c87808"},
        {"hue": 1257, "rgb": [240, 144, 0], "hex": "#f09000"},
        {"hue": 1258, "rgb": [240, 160, 8], "hex": "#f0a008"},
        {"hue": 1259, "rgb": [240, 184, 0], "hex": "#f0b800"},
        {"hue": 1260, "rgb": [248, 232, 64], "hex": "#f8e840"},
        {"hue": 1261, "rgb": [0, 0, 112], "hex": "#000070"},
        {"hue": 1262, "rgb": [0, 0, 160], "hex": "#0000a0"},
        {"hue": 1263, "rgb": [0, 40, 200], "hex": "#0028c8"},
        {"hue": 1264, "rgb": [0, 136, 216], "hex": "#0088d8"},
        {"hue": 1265, "rgb": [16, 136, 248], "hex": "#1088f8"},
        {"hue": 1266, "rgb": [0, 224, 248], "hex": "#00e0f8"},
        {"hue": 1267, "rgb": [8, 96, 0], "hex": "#086000"},
        {"hue": 1268, "rgb": [8, 176, 8], "hex": "#08b008"},
        {"hue": 1270, "rgb": [88, 216, 8], "hex": "#58d808"},
        {"hue": 1271, "rgb": [8, 232, 64], "hex": "#08e840"},
        {"hue": 1272, "rgb": [0, 248, 80], "hex": "#00f850"},
        {"hue": 1273, "rgb": [96, 0, 88], "hex": "#600058"},
        {"hue": 1274, "rgb": [128, 0, 128], "hex": "#800080"},
        {"hue": 1275, "rgb": [200, 0, 184], "hex": "#c800b8"},
        {"hue": 1276, "rgb": [224, 48, 160], "hex": "#e030a0"},
        {"hue": 1277, "rgb": [200, 80, 192], "hex": "#c850c0"},
        {"hue": 1278, "rgb": [224, 160, 216], "hex": "#e0a0d8"},
        {"hue": 1279, "rgb": [0, 0, 0], "hex": "#000000"},
        {"hue": 1281, "rgb": [248, 208, 0], "hex": "#f8d000"},
        {"hue": 1282, "rgb": [0, 112, 248], "hex": "#0070f8"},
        {"hue": 1283, "rgb": [0, 216, 248], "hex": "#00d8f8"},
        {"hue": 1284, "rgb": [0, 160, 216], "hex": "#00a0d8"},
        {"hue": 1286, "rgb": [8, 224, 192], "hex": "#08e0c0"},
        {"hue": 1287, "rgb": [0, 216, 232], "hex": "#00d8e8"},
        {"hue": 1288, "rgb": [248, 0, 8], "hex": "#f80008"},
        {"hue": 1289, "rgb": [248, 0, 224], "hex": "#f800e0"},
        {"hue": 1298, "rgb": [16, 184, 160], "hex": "#10b8a0"},
        {"hue": 1299, "rgb": [16, 248, 104], "hex": "#10f868"},
        {"hue": 1302, "rgb": [168, 168, 200], "hex": "#a8a8c8"},
        {"hue": 1303, "rgb": [152, 152, 192], "hex": "#9898c0"},
        {"hue": 1304, "rgb": [144, 144, 176], "hex": "#9090b0"},
        {"hue": 1305, "rgb": [136, 136, 168], "hex": "#8888a8"},
        {"hue": 1307, "rgb": [112, 112, 144], "hex": "#707090"},
        {"hue": 1308, "rgb": [96, 96, 136], "hex": "#606088"},
        {"hue": 1309, "rgb": [88, 88, 120], "hex": "#585878"},
        {"hue": 1310, "rgb": [176, 184, 232], "hex": "#b0b8e8"},
        {"hue": 1311, "rgb": [160, 168, 224], "hex": "#a0a8e0"},
        {"hue": 1312, "rgb": [144, 152, 208], "hex": "#9098d0"},
        {"hue": 1313, "rgb": [136, 144, 200], "hex": "#8890c8"},
        {"hue": 1314, "rgb": [128, 136, 184], "hex": "#8088b8"},
        {"hue": 1315, "rgb": [112, 120, 176], "hex": "#7078b0"},
        {"hue": 1316, "rgb": [104, 112, 160], "hex": "#6870a0"},
        {"hue": 1317, "rgb": [88, 96, 152], "hex": "#586098"},
        {"hue": 1318, "rgb": [80, 88, 136], "hex": "#505888"},
        {"hue": 1319, "rgb": [168, 184, 240], "hex": "#a8b8f0"},
        {"hue": 1320, "rgb": [152, 168, 240], "hex": "#98a8f0"},
        {"hue": 1321, "rgb": [136, 152, 224], "hex": "#8898e0"},
        {"hue": 1322, "rgb": [128, 144, 216], "hex": "#8090d8"},
        {"hue": 1323, "rgb": [120, 136, 200], "hex": "#7888c8"},
        {"hue": 1324, "rgb": [112, 120, 192], "hex": "#7078c0"},
        {"hue": 1325, "rgb": [96, 112, 184], "hex": "#6070b8"},
        {"hue": 1326, "rgb": [88, 96, 168], "hex": "#5860a8"},
        {"hue": 1327, "rgb": [72, 88, 160], "hex": "#4858a0"},
        {"hue": 1328, "rgb": [160, 184, 232], "hex": "#a0b8e8"},
        {"hue": 1329, "rgb": [144, 176, 224], "hex": "#90b0e0"},
        {"hue": 1330, "rgb": [136, 160, 208], "hex": "#88a0d0"},
        {"hue": 1331, "rgb": [120, 152, 200], "hex": "#7898c8"},
        {"hue": 1332, "rgb": [112, 144, 184], "hex": "#7090b8"},
        {"hue": 1333, "rgb": [104, 128, 176], "hex": "#6880b0"},
        {"hue": 1334, "rgb": [88, 120, 168], "hex": "#5878a8"},
        {"hue": 1335, "rgb": [72, 104, 152], "hex": "#486898"},
        {"hue": 1336, "rgb": [64, 96, 144], "hex": "#406090"},
        {"hue": 1337, "rgb": [168, 184, 208], "hex": "#a8b8d0"},
        {"hue": 1338, "rgb": [152, 176, 200], "hex": "#98b0c8"},
        {"hue": 1339, "rgb": [136, 160, 184], "hex": "#88a0b8"},
        {"hue": 1340, "rgb": [128, 152, 176], "hex": "#8098b0"},
        {"hue": 1342, "rgb": [112, 128, 152], "hex": "#708098"},
        {"hue": 1343, "rgb": [96, 120, 136], "hex": "#607888"},
        {"hue": 1344, "rgb": [88, 104, 128], "hex": "#586880"},
        {"hue": 1346, "rgb": [152, 192, 216], "hex": "#98c0d8"},
        {"hue": 1347, "rgb": [136, 184, 200], "hex": "#88b8c8"},
        {"hue": 1348, "rgb": [128, 168, 192], "hex": "#80a8c0"},
        {"hue": 1349, "rgb": [112, 160, 176], "hex": "#70a0b0"},
        {"hue": 1350, "rgb": [104, 144, 168], "hex": "#6890a8"},
        {"hue": 1351, "rgb": [96, 136, 160], "hex": "#6088a0"},
        {"hue": 1352, "rgb": [80, 120, 144], "hex": "#507890"},
        {"hue": 1353, "rgb": [72, 112, 136], "hex": "#487088"},
        {"hue": 1360, "rgb": [232, 216, 56], "hex": "#e8d838"},
        {"hue": 1361, "rgb": [176, 176, 240], "hex": "#b0b0f0"},
        {"hue": 1362, "rgb": [144, 144, 232], "hex": "#9090e8"},
        {"hue": 1363, "rgb": [128, 128, 248], "hex": "#8080f8"},
        {"hue": 1364, "rgb": [104, 104, 240], "hex": "#6868f0"},
        {"hue": 1365, "rgb": [80, 160, 224], "hex": "#50a0e0"},
        {"hue": 1366, "rgb": [32, 184, 248], "hex": "#20b8f8"},
        {"hue": 1396, "rgb": [24, 56, 224], "hex": "#1838e0"},
        {"hue": 1401, "rgb": [168, 192, 192], "hex": "#a8c0c0"},
        {"hue": 1403, "rgb": [144, 160, 168], "hex": "#90a0a8"},
        {"hue": 1404, "rgb": [128, 152, 160], "hex": "#8098a0"},
        {"hue": 1405, "rgb": [120, 144, 144], "hex": "#789090"},
        {"hue": 1406, "rgb": [112, 136, 136], "hex": "#708888"},
        {"hue": 1407, "rgb": [96, 120, 128], "hex": "#607880"},
        {"hue": 1408, "rgb": [88, 112, 112], "hex": "#587070"},
        {"hue": 1409, "rgb": [72, 96, 104], "hex": "#486068"},
        {"hue": 1410, "rgb": [160, 200, 184], "hex": "#a0c8b8"},
        {"hue": 1411, "rgb": [144, 184, 168], "hex": "#90b8a8"},
        {"hue": 1412, "rgb": [128, 176, 160], "hex": "#80b0a0"},
        {"hue": 1414, "rgb": [112, 152, 136], "hex": "#709888"},
        {"hue": 1415, "rgb": [96, 144, 128], "hex": "#609080"},
        {"hue": 1416, "rgb": [88, 128, 112], "hex": "#588070"},
        {"hue": 1417, "rgb": [72, 120, 104], "hex": "#487868"},
        {"hue": 1418, "rgb": [64, 104, 88], "hex": "#406858"},
        {"hue": 1419, "rgb": [144, 208, 168], "hex": "#90d0a8"},
        {"hue": 1420, "rgb": [136, 192, 160], "hex": "#88c0a0"},
        {"hue": 1421, "rgb": [120, 176, 144], "hex": "#78b090"},
        {"hue": 1422, "rgb": [112, 168, 136], "hex": "#70a888"},
        {"hue": 1423, "rgb": [96, 160, 128], "hex": "#60a080"},
        {"hue": 1424, "rgb": [88, 152, 112], "hex": "#589870"},
        {"hue": 1425, "rgb": [80, 136, 104], "hex": "#508868"},
        {"hue": 1426, "rgb": [64, 128, 88], "hex": "#408058"},
        {"hue": 1427, "rgb": [56, 112, 80], "hex": "#387050"},
        {"hue": 1428, "rgb": [168, 200, 160], "hex": "#a8c8a0"},
        {"hue": 1429, "rgb": [152, 184, 144], "hex": "#98b890"},
        {"hue": 1430, "rgb": [144, 168, 136], "hex": "#90a888"},
        {"hue": 1432, "rgb": [120, 152, 112], "hex": "#789870"},
        {"hue": 1433, "rgb": [112, 144, 104], "hex": "#709068"},
        {"hue": 1434, "rgb": [96, 128, 88], "hex": "#608058"},
        {"hue": 1435, "rgb": [88, 120, 80], "hex": "#587850"},
        {"hue": 1436, "rgb": [72, 104, 64], "hex": "#486840"},
        {"hue": 1437, "rgb": [184, 192, 136], "hex": "#b8c088"},
        {"hue": 1438, "rgb": [168, 184, 120], "hex": "#a8b878"},
        {"hue": 1439, "rgb": [152, 168, 112], "hex": "#98a870"},
        {"hue": 1440, "rgb": [144, 160, 96], "hex": "#90a060"},
        {"hue": 1441, "rgb": [136, 144, 88], "hex": "#889058"},
        {"hue": 1442, "rgb": [128, 136, 80], "hex": "#808850"},
        {"hue": 1443, "rgb": [112, 120, 64], "hex": "#707840"},
        {"hue": 1444, "rgb": [104, 112, 56], "hex": "#687038"},
        {"hue": 1445, "rgb": [88, 96, 40], "hex": "#586028"},
        {"hue": 1446, "rgb": [200, 184, 112], "hex": "#c8b870"},
        {"hue": 1447, "rgb": [200, 176, 104], "hex": "#c8b068"},
        {"hue": 1448, "rgb": [176, 160, 88], "hex": "#b0a058"},
        {"hue": 1449, "rgb": [168, 152, 80], "hex": "#a89850"},
        {"hue": 1450, "rgb": [152, 144, 64], "hex": "#989040"},
        {"hue": 1451, "rgb": [144, 128, 56], "hex": "#908038"},
        {"hue": 1452, "rgb": [136, 120, 48], "hex": "#887830"},
        {"hue": 1453, "rgb": [120, 104, 32], "hex": "#786820"},
        {"hue": 1454, "rgb": [112, 96, 24], "hex": "#706018"},
        {"hue": 1456, "rgb": [0, 192, 64], "hex": "#00c040"},
        {"hue": 1465, "rgb": [224, 24, 0], "hex": "#e01800"},
        {"hue": 1466, "rgb": [16, 248, 208], "hex": "#10f8d0"},
        {"hue": 1472, "rgb": [224, 184, 128], "hex": "#e0b880"},
        {"hue": 1474, "rgb": [16, 248, 136], "hex": "#10f888"},
        {"hue": 1491, "rgb": [112, 120, 128], "hex": "#707880"},
        {"hue": 1501, "rgb": [240, 168, 96], "hex": "#f0a860"},
        {"hue": 1502, "rgb": [240, 152, 80], "hex": "#f09850"},
        {"hue": 1503, "rgb": [224, 144, 64], "hex": "#e09040"},
        {"hue": 1504, "rgb": [216, 128, 56], "hex": "#d88038"},
        {"hue": 1505, "rgb": [208, 120, 48], "hex": "#d07830"},
        {"hue": 1506, "rgb": [192, 112, 32], "hex": "#c07020"},
        {"hue": 1507, "rgb": [184, 96, 24], "hex": "#b86018"},
        {"hue": 1508, "rgb": [168, 88, 8], "hex": "#a85808"},
        {"hue": 1509, "rgb": [160, 72, 8], "hex": "#a04808"},
        {"hue": 1511, "rgb": [232, 160, 88], "hex": "#e8a058"},
        {"hue": 1512, "rgb": [216, 144, 72], "hex": "#d89048"},
        {"hue": 1513, "rgb": [208, 136, 64], "hex": "#d08840"},
        {"hue": 1514, "rgb": [200, 120, 56], "hex": "#c87838"},
        {"hue": 1515, "rgb": [184, 112, 40], "hex": "#b87028"},
        {"hue": 1516, "rgb": [176, 96, 32], "hex": "#b06020"},
        {"hue": 1517, "rgb": [160, 88, 16], "hex": "#a05810"},
        {"hue": 1518, "rgb": [152, 72, 8], "hex": "#984808"},
        {"hue": 1519, "rgb": [232, 168, 120], "hex": "#e8a878"},
        {"hue": 1520, "rgb": [224, 160, 104], "hex": "#e0a068"},
        {"hue": 1521, "rgb": [208, 144, 96], "hex": "#d09060"},
        {"hue": 1522, "rgb": [200, 136, 80], "hex": "#c88850"},
        {"hue": 1523, "rgb": [192, 128, 72], "hex": "#c08048"},
        {"hue": 1524, "rgb": [184, 112, 64], "hex": "#b87040"},
        {"hue": 1525, "rgb": [168, 104, 48], "hex": "#a86830"},
        {"hue": 1526, "rgb": [160, 88, 40], "hex": "#a05828"},
        {"hue": 1527, "rgb": [144, 80, 24], "hex": "#905018"},
        {"hue": 1528, "rgb": [240, 168, 120], "hex": "#f0a878"},
        {"hue": 1529, "rgb": [232, 152, 112], "hex": "#e89870"},
        {"hue": 1530, "rgb": [216, 136, 96], "hex": "#d88860"},
        {"hue": 1531, "rgb": [208, 128, 88], "hex": "#d08058"},
        {"hue": 1532, "rgb": [200, 120, 72], "hex": "#c87848"},
        {"hue": 1533, "rgb": [192, 104, 64], "hex": "#c06840"},
        {"hue": 1534, "rgb": [176, 96, 48], "hex": "#b06030"},
        {"hue": 1535, "rgb": [168, 80, 40], "hex": "#a85028"},
        {"hue": 1536, "rgb": [152, 72, 24], "hex": "#984818"},
        {"hue": 1537, "rgb": [240, 160, 128], "hex": "#f0a080"},
        {"hue": 1538, "rgb": [232, 152, 120], "hex": "#e89878"},
        {"hue": 1539, "rgb": [216, 136, 104], "hex": "#d88868"},
        {"hue": 1540, "rgb": [208, 128, 96], "hex": "#d08060"},
        {"hue": 1541, "rgb": [200, 120, 80], "hex": "#c87850"},
        {"hue": 1542, "rgb": [184, 104, 72], "hex": "#b86848"},
        {"hue": 1543, "rgb": [176, 96, 64], "hex": "#b06040"},
        {"hue": 1544, "rgb": [160, 80, 48], "hex": "#a05030"},
        {"hue": 1545, "rgb": [152, 72, 40], "hex": "#984828"},
        {"hue": 1546, "rgb": [240, 160, 120], "hex": "#f0a078"},
        {"hue": 1547, "rgb": [240, 144, 104], "hex": "#f09068"},
        {"hue": 1548, "rgb": [224, 128, 88], "hex": "#e08058"},
        {"hue": 1549, "rgb": [216, 120, 80], "hex": "#d87850"},
        {"hue": 1550, "rgb": [208, 112, 64], "hex": "#d07040"},
        {"hue": 1551, "rgb": [200, 96, 56], "hex": "#c86038"},
        {"hue": 1552, "rgb": [192, 88, 40], "hex": "#c05828"},
        {"hue": 1553, "rgb": [176, 72, 32], "hex": "#b04820"},
        {"hue": 1554, "rgb": [168, 64, 24], "hex": "#a84018"},
        {"hue": 1559, "rgb": [240, 128, 0], "hex": "#f08000"},
        {"hue": 1570, "rgb": [120, 248, 0], "hex": "#78f800"},
        {"hue": 1577, "rgb": [16, 248, 232], "hex": "#10f8e8"},
        {"hue": 1582, "rgb": [128, 0, 88], "hex": "#800058"},
        {"hue": 1589, "rgb": [0, 64, 48], "hex": "#004030"},
        {"hue": 1602, "rgb": [232, 152, 136], "hex": "#e89888"},
        {"hue": 1603, "rgb": [216, 136, 120], "hex": "#d88878"},
        {"hue": 1604, "rgb": [208, 128, 112], "hex": "#d08070"},
        {"hue": 1605, "rgb": [200, 112, 96], "hex": "#c87060"},
        {"hue": 1606, "rgb": [184, 104, 88], "hex": "#b86858"},
        {"hue": 1607, "rgb": [176, 88, 80], "hex": "#b05850"},
        {"hue": 1608, "rgb": [160, 80, 64], "hex": "#a05040"},
        {"hue": 1609, "rgb": [152, 64, 56], "hex": "#984038"},
        {"hue": 1611, "rgb": [240, 144, 120], "hex": "#f09078"},
        {"hue": 1612, "rgb": [240, 128, 104], "hex": "#f08068"},
        {"hue": 1613, "rgb": [224, 120, 88], "hex": "#e07858"},
        {"hue": 1614, "rgb": [216, 112, 80], "hex": "#d87050"},
        {"hue": 1615, "rgb": [208, 96, 72], "hex": "#d06048"},
        {"hue": 1616, "rgb": [192, 88, 56], "hex": "#c05838"},
        {"hue": 1617, "rgb": [184, 72, 48], "hex": "#b84830"},
        {"hue": 1618, "rgb": [168, 64, 32], "hex": "#a84020"},
        {"hue": 1620, "rgb": [240, 144, 128], "hex": "#f09080"},
        {"hue": 1621, "rgb": [232, 128, 112], "hex": "#e88070"},
        {"hue": 1622, "rgb": [224, 120, 96], "hex": "#e07860"},
        {"hue": 1623, "rgb": [216, 104, 88], "hex": "#d86858"},
        {"hue": 1625, "rgb": [192, 88, 64], "hex": "#c05840"},
        {"hue": 1626, "rgb": [176, 72, 56], "hex": "#b04838"},
        {"hue": 1627, "rgb": [168, 64, 40], "hex": "#a84028"},
        {"hue": 1628, "rgb": [240, 160, 152], "hex": "#f0a098"},
        {"hue": 1630, "rgb": [240, 120, 104], "hex": "#f07868"},
        {"hue": 1632, "rgb": [232, 104, 88], "hex": "#e86858"},
        {"hue": 1634, "rgb": [208, 80, 64], "hex": "#d05040"},
        {"hue": 1635, "rgb": [192, 64, 48], "hex": "#c04030"},
        {"hue": 1636, "rgb": [184, 56, 40], "hex": "#b83828"},
        {"hue": 1638, "rgb": [240, 144, 136], "hex": "#f09088"},
        {"hue": 1639, "rgb": [240, 120, 120], "hex": "#f07878"},
        {"hue": 1640, "rgb": [240, 104, 104], "hex": "#f06868"},
        {"hue": 1641, "rgb": [232, 96, 88], "hex": "#e86058"},
        {"hue": 1642, "rgb": [224, 88, 80], "hex": "#e05850"},
        {"hue": 1643, "rgb": [216, 72, 72], "hex": "#d84848"},
        {"hue": 1644, "rgb": [200, 64, 56], "hex": "#c84038"},
        {"hue": 1645, "rgb": [192, 48, 48], "hex": "#c03030"},
        {"hue": 1649, "rgb": [240, 112, 104], "hex": "#f07068"},
        {"hue": 1650, "rgb": [224, 96, 96], "hex": "#e06060"},
        {"hue": 1651, "rgb": [216, 88, 88], "hex": "#d85858"},
        {"hue": 1652, "rgb": [208, 80, 72], "hex": "#d05048"},
        {"hue": 1653, "rgb": [192, 64, 64], "hex": "#c04040"},
        {"hue": 1654, "rgb": [184, 56, 48], "hex": "#b83830"},
        {"hue": 1663, "rgb": [96, 128, 0], "hex": "#608000"},
        {"hue": 1664, "rgb": [192, 0, 80], "hex": "#c00050"},
        {"hue": 1674, "rgb": [248, 240, 208], "hex": "#f8f0d0"},
        {"hue": 1675, "rgb": [16, 64, 64], "hex": "#104040"},
        {"hue": 1676, "rgb": [248, 240, 216], "hex": "#f8f0d8"},
        {"hue": 1685, "rgb": [8, 248, 200], "hex": "#08f8c8"},
        {"hue": 1689, "rgb": [120, 136, 128], "hex": "#788880"},
        {"hue": 1693, "rgb": [120, 240, 0], "hex": "#78f000"},
        {"hue": 1701, "rgb": [216, 184, 88], "hex": "#d8b858"},
        {"hue": 1702, "rgb": [208, 168, 72], "hex": "#d0a848"},
        {"hue": 1703, "rgb": [192, 160, 64], "hex": "#c0a040"},
        {"hue": 1704, "rgb": [184, 144, 48], "hex": "#b89030"},
        {"hue": 1705, "rgb": [176, 136, 40], "hex": "#b08828"},
        {"hue": 1706, "rgb": [160, 128, 32], "hex": "#a08020"},
        {"hue": 1708, "rgb": [136, 104, 8], "hex": "#886808"},
        {"hue": 1709, "rgb": [128, 88, 0], "hex": "#805800"},
        {"hue": 1710, "rgb": [224, 176, 96], "hex": "#e0b060"},
        {"hue": 1711, "rgb": [216, 168, 80], "hex": "#d8a850"},
        {"hue": 1712, "rgb": [200, 152, 64], "hex": "#c89840"},
        {"hue": 1713, "rgb": [192, 144, 56], "hex": "#c09038"},
        {"hue": 1715, "rgb": [168, 120, 32], "hex": "#a87820"},
        {"hue": 1716, "rgb": [160, 112, 24], "hex": "#a07018"},
        {"hue": 1717, "rgb": [144, 96, 8], "hex": "#906008"},
        {"hue": 1719, "rgb": [240, 176, 56], "hex": "#f0b038"},
        {"hue": 1720, "rgb": [232, 168, 48], "hex": "#e8a830"},
        {"hue": 1721, "rgb": [216, 152, 32], "hex": "#d89820"},
        {"hue": 1722, "rgb": [208, 144, 24], "hex": "#d09018"},
        {"hue": 1723, "rgb": [192, 136, 16], "hex": "#c08810"},
        {"hue": 1724, "rgb": [184, 120, 8], "hex": "#b87808"},
        {"hue": 1726, "rgb": [152, 96, 0], "hex": "#986000"},
        {"hue": 1727, "rgb": [136, 88, 0], "hex": "#885800"},
        {"hue": 1728, "rgb": [232, 176, 104], "hex": "#e8b068"},
        {"hue": 1729, "rgb": [216, 160, 96], "hex": "#d8a060"},
        {"hue": 1730, "rgb": [200, 152, 80], "hex": "#c89850"},
        {"hue": 1731, "rgb": [192, 136, 72], "hex": "#c08848"},
        {"hue": 1732, "rgb": [184, 128, 56], "hex": "#b88038"},
        {"hue": 1733, "rgb": [168, 120, 48], "hex": "#a87830"},
        {"hue": 1734, "rgb": [160, 104, 32], "hex": "#a06820"},
        {"hue": 1735, "rgb": [144, 96, 24], "hex": "#906018"},
        {"hue": 1736, "rgb": [136, 80, 8], "hex": "#885008"},
        {"hue": 1737, "rgb": [240, 168, 88], "hex": "#f0a858"},
        {"hue": 1738, "rgb": [232, 160, 80], "hex": "#e8a050"},
        {"hue": 1739, "rgb": [216, 144, 64], "hex": "#d89040"},
        {"hue": 1740, "rgb": [208, 136, 56], "hex": "#d08838"},
        {"hue": 1741, "rgb": [200, 128, 40], "hex": "#c88028"},
        {"hue": 1742, "rgb": [184, 112, 32], "hex": "#b87020"},
        {"hue": 1743, "rgb": [176, 104, 24], "hex": "#b06818"},
        {"hue": 1744, "rgb": [160, 88, 8], "hex": "#a05808"},
        {"hue": 1745, "rgb": [152, 80, 8], "hex": "#985008"},
        {"hue": 1746, "rgb": [232, 176, 112], "hex": "#e8b070"},
        {"hue": 1748, "rgb": [208, 144, 80], "hex": "#d09050"},
        {"hue": 1750, "rgb": [184, 128, 64], "hex": "#b88040"},
        {"hue": 1751, "rgb": [176, 112, 56], "hex": "#b07038"},
        {"hue": 1752, "rgb": [160, 104, 40], "hex": "#a06828"},
        {"hue": 1753, "rgb": [152, 88, 32], "hex": "#985820"},
        {"hue": 1754, "rgb": [136, 80, 16], "hex": "#885010"},
        {"hue": 1801, "rgb": [200, 184, 128], "hex": "#c8b880"},
        {"hue": 1802, "rgb": [192, 176, 120], "hex": "#c0b078"},
        {"hue": 1803, "rgb": [176, 160, 104], "hex": "#b0a068"},
        {"hue": 1804, "rgb": [168, 152, 96], "hex": "#a89860"},
        {"hue": 1805, "rgb": [160, 136, 88], "hex": "#a08858"},
        {"hue": 1806, "rgb": [144, 128, 72], "hex": "#908048"},
        {"hue": 1807, "rgb": [136, 112, 64], "hex": "#887040"},
        {"hue": 1808, "rgb": [120, 104, 48], "hex": "#786830"},
        {"hue": 1809, "rgb": [112, 88, 40], "hex": "#705828"},
        {"hue": 1810, "rgb": [216, 176, 120], "hex": "#d8b078"},
        {"hue": 1811, "rgb": [208, 168, 104], "hex": "#d0a868"},
        {"hue": 1812, "rgb": [192, 152, 96], "hex": "#c09860"},
        {"hue": 1813, "rgb": [184, 144, 80], "hex": "#b89050"},
        {"hue": 1814, "rgb": [168, 136, 72], "hex": "#a88848"},
        {"hue": 1815, "rgb": [160, 120, 64], "hex": "#a07840"},
        {"hue": 1816, "rgb": [152, 112, 48], "hex": "#987030"},
        {"hue": 1817, "rgb": [136, 96, 40], "hex": "#886028"},
        {"hue": 1818, "rgb": [128, 88, 24], "hex": "#805818"},
        {"hue": 1819, "rgb": [208, 176, 136], "hex": "#d0b088"},
        {"hue": 1821, "rgb": [184, 152, 104], "hex": "#b89868"},
        {"hue": 1822, "rgb": [176, 144, 96], "hex": "#b09060"},
        {"hue": 1824, "rgb": [152, 120, 80], "hex": "#987850"},
        {"hue": 1826, "rgb": [128, 96, 56], "hex": "#806038"},
        {"hue": 1829, "rgb": [200, 168, 128], "hex": "#c8a880"},
        {"hue": 1830, "rgb": [184, 152, 112], "hex": "#b89870"},
        {"hue": 1831, "rgb": [176, 144, 104], "hex": "#b09068"},
        {"hue": 1832, "rgb": [160, 136, 96], "hex": "#a08860"},
        {"hue": 1834, "rgb": [144, 112, 72], "hex": "#907048"},
        {"hue": 1837, "rgb": [216, 176, 136], "hex": "#d8b088"},
        {"hue": 1838, "rgb": [208, 168, 128], "hex": "#d0a880"},
        {"hue": 1839, "rgb": [192, 152, 112], "hex": "#c09870"},
        {"hue": 1841, "rgb": [168, 128, 88], "hex": "#a88058"},
        {"hue": 1842, "rgb": [160, 120, 80], "hex": "#a07850"},
        {"hue": 1844, "rgb": [136, 96, 56], "hex": "#886038"},
        {"hue": 1845, "rgb": [120, 80, 40], "hex": "#785028"},
        {"hue": 1846, "rgb": [224, 176, 136], "hex": "#e0b088"},
        {"hue": 1847, "rgb": [208, 160, 120], "hex": "#d0a078"},
        {"hue": 1848, "rgb": [200, 144, 104], "hex": "#c89068"},
        {"hue": 1849, "rgb": [184, 136, 96], "hex": "#b88860"},
        {"hue": 1850, "rgb": [176, 128, 88], "hex": "#b08058"},
        {"hue": 1851, "rgb": [168, 120, 80], "hex": "#a87850"},
        {"hue": 1852, "rgb": [152, 104, 64], "hex": "#986840"},
        {"hue": 1853, "rgb": [144, 96, 56], "hex": "#906038"},
        {"hue": 1854, "rgb": [128, 80, 40], "hex": "#805028"},
        {"hue": 1855, "rgb": [240, 168, 128], "hex": "#f0a880"},
        {"hue": 1859, "rgb": [192, 120, 80], "hex": "#c07850"},
        {"hue": 1860, "rgb": [184, 112, 72], "hex": "#b87048"},
        {"hue": 1861, "rgb": [176, 96, 56], "hex": "#b06038"},
        {"hue": 1862, "rgb": [160, 88, 48], "hex": "#a05830"},
        {"hue": 1863, "rgb": [152, 72, 32], "hex": "#984820"},
        {"hue": 1864, "rgb": [224, 168, 136], "hex": "#e0a888"},
        {"hue": 1865, "rgb": [216, 160, 128], "hex": "#d8a080"},
        {"hue": 1866, "rgb": [200, 144, 112], "hex": "#c89070"},
        {"hue": 1867, "rgb": [192, 136, 104], "hex": "#c08868"},
        {"hue": 1869, "rgb": [168, 112, 80], "hex": "#a87050"},
        {"hue": 1870, "rgb": [160, 104, 72], "hex": "#a06848"},
        {"hue": 1871, "rgb": [144, 88, 56], "hex": "#905838"},
        {"hue": 1872, "rgb": [136, 80, 48], "hex": "#885030"},
        {"hue": 1873, "rgb": [200, 176, 160], "hex": "#c8b0a0"},
        {"hue": 1874, "rgb": [200, 168, 152], "hex": "#c8a898"},
        {"hue": 1875, "rgb": [176, 152, 136], "hex": "#b09888"},
        {"hue": 1876, "rgb": [168, 144, 128], "hex": "#a89080"},
        {"hue": 1877, "rgb": [152, 128, 112], "hex": "#988070"},
        {"hue": 1878, "rgb": [144, 120, 104], "hex": "#907868"},
        {"hue": 1879, "rgb": [136, 112, 96], "hex": "#887060"},
        {"hue": 1880, "rgb": [120, 96, 80], "hex": "#786050"},
        {"hue": 1882, "rgb": [192, 184, 176], "hex": "#c0b8b0"},
        {"hue": 1883, "rgb": [184, 168, 160], "hex": "#b8a8a0"},
        {"hue": 1884, "rgb": [168, 152, 144], "hex": "#a89890"},
        {"hue": 1885, "rgb": [160, 144, 136], "hex": "#a09088"},
        {"hue": 1886, "rgb": [144, 136, 128], "hex": "#908880"},
        {"hue": 1887, "rgb": [136, 120, 112], "hex": "#887870"},
        {"hue": 1889, "rgb": [112, 96, 88], "hex": "#706058"},
        {"hue": 1891, "rgb": [184, 184, 184], "hex": "#b8b8b8"},
        {"hue": 1893, "rgb": [160, 160, 160], "hex": "#a0a0a0"},
        {"hue": 1895, "rgb": [136, 136, 136], "hex": "#888888"},
        {"hue": 1896, "rgb": [128, 128, 128], "hex": "#808080"},
        {"hue": 1897, "rgb": [112, 112, 112], "hex": "#707070"},
        {"hue": 1898, "rgb": [104, 104, 104], "hex": "#686868"},
        {"hue": 1900, "rgb": [184, 184, 192], "hex": "#b8b8c0"},
        {"hue": 1901, "rgb": [168, 168, 184], "hex": "#a8a8b8"},
        {"hue": 1902, "rgb": [160, 160, 168], "hex": "#a0a0a8"},
        {"hue": 1904, "rgb": [136, 136, 144], "hex": "#888890"},
        {"hue": 1905, "rgb": [128, 128, 136], "hex": "#808088"},
        {"hue": 1906, "rgb": [112, 112, 120], "hex": "#707078"},
        {"hue": 1907, "rgb": [104, 104, 112], "hex": "#686870"},
        {"hue": 1908, "rgb": [88, 88, 96], "hex": "#585860"},
        {"hue": 2001, "rgb": [208, 224, 104], "hex": "#d0e068"},
        {"hue": 2002, "rgb": [184, 224, 96], "hex": "#b8e060"},
        {"hue": 2003, "rgb": [168, 224, 96], "hex": "#a8e060"},
        {"hue": 2004, "rgb": [152, 192, 88], "hex": "#98c058"},
        {"hue": 2005, "rgb": [128, 176, 80], "hex": "#80b050"},
        {"hue": 2006, "rgb": [96, 144, 48], "hex": "#609030"},
        {"hue": 2007, "rgb": [240, 208, 152], "hex": "#f0d098"},
        {"hue": 2008, "rgb": [232, 192, 112], "hex": "#e8c070"},
        {"hue": 2009, "rgb": [224, 184, 96], "hex": "#e0b860"},
        {"hue": 2010, "rgb": [208, 168, 48], "hex": "#d0a830"},
        {"hue": 2013, "rgb": [232, 168, 136], "hex": "#e8a888"},
        {"hue": 2014, "rgb": [232, 160, 120], "hex": "#e8a078"},
        {"hue": 2015, "rgb": [224, 144, 104], "hex": "#e09068"},
        {"hue": 2016, "rgb": [200, 112, 72], "hex": "#c87048"},
        {"hue": 2017, "rgb": [160, 128, 80], "hex": "#a08050"},
        {"hue": 2018, "rgb": [128, 96, 64], "hex": "#806040"},
        {"hue": 2020, "rgb": [64, 64, 64], "hex": "#404040"},
        {"hue": 2021, "rgb": [72, 72, 72], "hex": "#484848"},
        {"hue": 2022, "rgb": [80, 80, 80], "hex": "#505050"},
        {"hue": 2024, "rgb": [96, 96, 96], "hex": "#606060"},
        {"hue": 2031, "rgb": [152, 152, 152], "hex": "#989898"},
        {"hue": 2034, "rgb": [176, 176, 176], "hex": "#b0b0b0"},
        {"hue": 2037, "rgb": [200, 200, 200], "hex": "#c8c8c8"},
        {"hue": 2038, "rgb": [208, 208, 208], "hex": "#d0d0d0"},
        {"hue": 2039, "rgb": [216, 216, 216], "hex": "#d8d8d8"},
        {"hue": 2040, "rgb": [224, 224, 224], "hex": "#e0e0e0"},
        {"hue": 2041, "rgb": [232, 232, 232], "hex": "#e8e8e8"},
        {"hue": 2051, "rgb": [48, 48, 48], "hex": "#303030"},
        {"hue": 2052, "rgb": [40, 40, 40], "hex": "#282828"},
        {"hue": 2053, "rgb": [32, 32, 32], "hex": "#202020"},
        {"hue": 2054, "rgb": [24, 24, 24], "hex": "#181818"},
        {"hue": 2055, "rgb": [16, 16, 16], "hex": "#101010"},
        {"hue": 2056, "rgb": [8, 8, 8], "hex": "#080808"},
        {"hue": 2102, "rgb": [192, 192, 200], "hex": "#c0c0c8"},
        {"hue": 2103, "rgb": [176, 176, 184], "hex": "#b0b0b8"},
        {"hue": 2110, "rgb": [192, 160, 104], "hex": "#c0a068"},
        {"hue": 2114, "rgb": [240, 152, 8], "hex": "#f09808"},
        {"hue": 2115, "rgb": [232, 144, 96], "hex": "#e89060"},
        {"hue": 2116, "rgb": [216, 104, 56], "hex": "#d86838"},
        {"hue": 2117, "rgb": [240, 72, 48], "hex": "#f04830"},
        {"hue": 2118, "rgb": [208, 48, 48], "hex": "#d03030"},
        {"hue": 2119, "rgb": [168, 208, 240], "hex": "#a8d0f0"},
        {"hue": 2120, "rgb": [152, 200, 240], "hex": "#98c8f0"},
        {"hue": 2121, "rgb": [144, 184, 240], "hex": "#90b8f0"},
        {"hue": 2122, "rgb": [136, 160, 240], "hex": "#88a0f0"},
        {"hue": 2123, "rgb": [88, 136, 216], "hex": "#5888d8"},
        {"hue": 2124, "rgb": [72, 128, 200], "hex": "#4880c8"},
        {"hue": 2125, "rgb": [240, 208, 0], "hex": "#f0d000"},
        {"hue": 2126, "rgb": [192, 224, 48], "hex": "#c0e030"},
        {"hue": 2127, "rgb": [160, 216, 72], "hex": "#a0d848"},
        {"hue": 2128, "rgb": [120, 192, 88], "hex": "#78c058"},
        {"hue": 2129, "rgb": [104, 160, 80], "hex": "#68a050"},
        {"hue": 2130, "rgb": [56, 128, 96], "hex": "#388060"},
        {"hue": 2201, "rgb": [240, 160, 136], "hex": "#f0a088"},
        {"hue": 2203, "rgb": [232, 128, 104], "hex": "#e88068"},
        {"hue": 2204, "rgb": [216, 120, 112], "hex": "#d87870"},
        {"hue": 2205, "rgb": [192, 96, 88], "hex": "#c06058"},
        {"hue": 2206, "rgb": [160, 64, 56], "hex": "#a04038"},
        {"hue": 2211, "rgb": [128, 168, 80], "hex": "#80a850"},
        {"hue": 2213, "rgb": [240, 208, 64], "hex": "#f0d040"},
        {"hue": 2214, "rgb": [232, 200, 56], "hex": "#e8c838"},
        {"hue": 2215, "rgb": [216, 192, 56], "hex": "#d8c038"},
        {"hue": 2219, "rgb": [176, 208, 232], "hex": "#b0d0e8"},
        {"hue": 2221, "rgb": [160, 192, 208], "hex": "#a0c0d0"},
        {"hue": 2222, "rgb": [136, 168, 184], "hex": "#88a8b8"},
        {"hue": 2223, "rgb": [112, 144, 160], "hex": "#7090a0"},
        {"hue": 2224, "rgb": [88, 112, 136], "hex": "#587088"},
        {"hue": 2307, "rgb": [240, 216, 184], "hex": "#f0d8b8"},
        {"hue": 2308, "rgb": [240, 200, 128], "hex": "#f0c880"},
        {"hue": 2309, "rgb": [232, 192, 120], "hex": "#e8c078"},
        {"hue": 2313, "rgb": [240, 192, 144], "hex": "#f0c090"},
        {"hue": 2314, "rgb": [240, 184, 128], "hex": "#f0b880"},
        {"hue": 2315, "rgb": [240, 168, 104], "hex": "#f0a868"},
        {"hue": 2316, "rgb": [200, 152, 96], "hex": "#c89860"},
        {"hue": 2317, "rgb": [184, 128, 72], "hex": "#b88048"},
        {"hue": 2318, "rgb": [160, 96, 48], "hex": "#a06030"},
        {"hue": 2401, "rgb": [200, 200, 208], "hex": "#c8c8d0"},
        {"hue": 2405, "rgb": [144, 136, 152], "hex": "#908898"},
        {"hue": 2406, "rgb": [112, 104, 120], "hex": "#706878"},
        {"hue": 2413, "rgb": [232, 200, 120], "hex": "#e8c878"},
        {"hue": 2414, "rgb": [224, 192, 112], "hex": "#e0c070"},
        {"hue": 2415, "rgb": [216, 176, 104], "hex": "#d8b068"},
        {"hue": 2416, "rgb": [192, 160, 80], "hex": "#c0a050"},
        {"hue": 2420, "rgb": [208, 192, 168], "hex": "#d0c0a8"},
        {"hue": 2422, "rgb": [176, 160, 136], "hex": "#b0a088"},
        {"hue": 2423, "rgb": [176, 152, 128], "hex": "#b09880"},
        {"hue": 2424, "rgb": [160, 144, 120], "hex": "#a09078"},
        {"hue": 2425, "rgb": [232, 192, 168], "hex": "#e8c0a8"},
        {"hue": 2427, "rgb": [216, 176, 152], "hex": "#d8b098"},
        {"hue": 2428, "rgb": [192, 152, 128], "hex": "#c09880"},
        {"hue": 2429, "rgb": [184, 152, 120], "hex": "#b89878"},
        {"hue": 2947, "rgb": [200, 248, 224], "hex": "#c8f8e0"},
        {"hue": 2951, "rgb": [232, 224, 208], "hex": "#e8e0d0"},
        {"hue": 2952, "rgb": [224, 208, 168], "hex": "#e0d0a8"},
        {"hue": 2953, "rgb": [240, 232, 224], "hex": "#f0e8e0"},
        {"hue": 2955, "rgb": [240, 224, 216], "hex": "#f0e0d8"},
        {"hue": 2956, "rgb": [224, 248, 240], "hex": "#e0f8f0"},
        {"hue": 2958, "rgb": [248, 240, 232], "hex": "#f8f0e8"},
        {"hue": 2963, "rgb": [216, 248, 224], "hex": "#d8f8e0"},
        {"hue": 2966, "rgb": [216, 248, 232], "hex": "#d8f8e8"},
        {"hue": 2967, "rgb": [248, 232, 216], "hex": "#f8e8d8"},
    ]

    @staticmethod
    def convertFromHueToHex(hue):
        isHueValid = Color.checkIfHueIsValid(hue)
        if not isHueValid:
            API.SysMsg("hue is not a valid UO Color")
            API.Stop()
        for color in Color.colors:
            if color["hue"] == hue:
                return color["hex"]

    @staticmethod
    def convertFromHexToHue(hex):
        isHexValid = Color.checkIfHexIsValid(hex)
        if not isHexValid:
            API.SysMsg("hex is not a valid UO Color")
            API.Stop()
        for color in Color.colors:
            if color["hex"].lower() == hex.lower():
                return color["hue"]

    @staticmethod
    def checkIfHueIsValid(hue):
        for color in Color.colors:
            if color["hue"] == hue:
                return True
        return False

    @staticmethod
    def checkIfHexIsValid(hex):
        if not hex.startswith("#"):
            hex = f"#{hex}"
        if not len(hex) == 7:
            API.SysMsg("hex must be length 7")
            API.Stop()
        for color in Color.colors:
            if color["hex"].lower() == hex.lower():
                return True
        return False


# =========== End of _Utils\Color.py ============#

# =========== Start of _Jsons\button_types.py ============#
buttonTypesStr = {
    "taming": {"hover": 24005, "normal": 24005, "pressed": 24005},
    "arrowDown": {"hover": 4504, "normal": 4504, "pressed": 4504},
    "arrowDownLeft": {"hover": 4505, "normal": 4505, "pressed": 4505},
    "arrowDownRight": {"hover": 4503, "normal": 4503, "pressed": 4503},
    "arrowLeft": {"hover": 4506, "normal": 4506, "pressed": 4506},
    "arrowLeftBlue": {"hover": 9706, "normal": 9706, "pressed": 9707},
    "arrowLeftGray": {"hover": 9766, "normal": 9766, "pressed": 9767},
    "arrowRight": {"hover": 4502, "normal": 4502, "pressed": 4502},
    "arrowRightBlue": {"hover": 9762, "normal": 9762, "pressed": 9763},
    "arrowRightGray": {"hover": 9702, "normal": 9702, "pressed": 9703},
    "arrowUp": {"hover": 4500, "normal": 4500, "pressed": 4500},
    "arrowUpLeft": {"hover": 4507, "normal": 4507, "pressed": 4507},
    "arrowUpRight": {"hover": 4501, "normal": 4501, "pressed": 4501},
    "bard": {"hover": 24004, "normal": 24004, "pressed": 24004},
    "cancel": {"hover": 242, "normal": 241, "pressed": 243},
    "caster": {"hover": 23014, "normal": 23014, "pressed": 23014},
    "check": {"hover": 5050, "normal": 5050, "pressed": 5051},
    "checkbox": {"hover": 9026, "normal": 9026, "pressed": 9027},
    "checkboxChecked": {"hover": 9027, "normal": 9027, "pressed": 9026},
    "checkboxDiamond": {"hover": 9723, "normal": 9721, "pressed": 9722},
    "default": {"hover": 2444, "normal": 2444, "pressed": 2443},
    "disable": {"hover": 4021, "normal": 4020, "pressed": 4021},
    "eye": {"hover": 1532, "normal": 1531, "pressed": 1532},
    "help": {"hover": 9999, "normal": 9999, "pressed": 9999},
    "isNotTameable": {"hover": 9997, "normal": 9997, "pressed": 9997},
    "isTameable": {"hover": 9998, "normal": 9998, "pressed": 9998},
    "okay": {"hover": 249, "normal": 247, "pressed": 248},
    "poisonnedSkull": {"hover": 39863, "normal": 39863, "pressed": 39863},
    "radio": {"hover": 9020, "normal": 9020, "pressed": 9021},
    "radioBlue": {"hover": 30085, "normal": 30083, "pressed": 30084},
    "radioGreen": {"hover": 11402, "normal": 11400, "pressed": 11401},
    "radioRed": {"hover": 11412, "normal": 11410, "pressed": 11411},
    "save": {"hover": 5202, "normal": 5202, "pressed": 5203},
    "skull": {"hover": 40320, "normal": 40320, "pressed": 40320},
    "skullWithCrown": {"hover": 40321, "normal": 40321, "pressed": 40321},
    "skullX": {"hover": 9804, "normal": 9804, "pressed": 9804},
    "squareX": {"hover": 40015, "normal": 40015, "pressed": 40015},
    "thief": {"hover": 23012, "normal": 23012, "pressed": 23012},
    "thief": {"hover": 23012, "normal": 23012, "pressed": 23012},
    "tracking": {"hover": 4009, "normal": 4008, "pressed": 4009},
    "wordOfDeath": {"hover": 23013, "normal": 23013, "pressed": 23013},
    "world": {"hover": 234, "normal": 234, "pressed": 234},
    "x": {"hover": 5052, "normal": 5052, "pressed": 5053},
}
# =========== End of _Jsons\button_types.py ============#

# =========== Start of _Utils\Gump.py ============#


class Gump:
    buttonTypes = Math.convertToHex(buttonTypesStr)

    def __init__(self, width, height, onCloseCb=None, withStatus=True):
        self.width = width
        self.height = height
        self.onCloseCb = onCloseCb
        self.withStatus = withStatus

        self.gump = API.CreateGump(True, True)
        self.subGumps = []
        self.bg = None
        self._running = True
        self.buttons = []
        self.skillTextBoxes = []
        self.pendingCallbacks = []
        self.tabGumps = {}

        self.gump.SetWidth(self.width)
        self.gump.SetHeight(self.height)
        self.gump.CenterXInViewPort()
        self.gump.CenterYInViewPort()
        self.borders = self._setBorders(0, 0, self.width, self.height)
        self._setBackground()

        if withStatus:
            self.statusLabel = API.CreateGumpLabel("Ready.")
            self.statusLabel.SetX(10)
            self.statusLabel.SetY(self.height - 30)
            self.gump.Add(self.statusLabel)

        self._lastCheckTime = time.time()
        self._checkInterval = 0.1

    def create(self):
        API.AddGump(self.gump)

    def tick(self):
        if not self._running:
            self._running = False
            if self.onCloseCb:
                self.onCloseCb()
            else:
                self.destroy()
                API.Stop()
            return

        now = time.time()
        if (now - self._lastCheckTime) >= self._checkInterval:
            self.checkValidateForm()
            self._checkEvents()
            self._lastCheckTime = now

    def tickSubGumps(self):
        for subGump, position, _ in self.subGumps:
            if subGump._running and not subGump.gump.IsDisposed:
                self._setSubGumpPosition(
                    subGump.gump, subGump.width, subGump.height, position
                )

    def destroy(self):
        if not self._running:
            return
        self._running = False
        for tab in self.tabGumps.values():
            try:
                if not tab.IsDisposed:
                    tab.Dispose()
            except:
                pass
        for subGump in self.subGumps:
            subGump.destroy()
        try:
            if not self.gump.IsDisposed:
                self.gump.Dispose()
        except Exception as e:
            API.SysMsg(f"Gump.Dispose failed: {e}", 33)
        API.SysMsg("Gump destroyed.", 66)

    def createProgressBar(self, x, y, height, width, current, total, title=""):
        elements = []

        # Avoid division by zero
        if total <= 0:
            total = 1

        # Title
        if title:
            label = self.addLabel(title, x, y)
            elements.append(label)
            y += 20

        # Background (light gray)
        bg = self.addColorBox(x, y, height, width, "#cccccc")
        elements.append(bg)

        # Purple fill (progress portion)
        ratio = max(0.0, min(1.0, current / total))
        fill_width = int(width * ratio)
        if fill_width > 0:
            fill = self.addColorBox(x, y, height, fill_width, "#4e009b")  # purple
            elements.append(fill)

        # Optional text overlay (e.g. “75 / 100”)
        progress_label = self.addLabel(
            f"{int(current)} / {int(total)}",
            x + width // 2 - 15,
            y + (height // 2) - 7,
            1,
        )
        elements.append(progress_label)

        return elements

    def createStackedBarChart(self, x, y, height, width, count, title=""):
        elements = []

        # title
        label = self.addLabel(title, x, y)
        elements.append(label)
        y += 20

        # Background bar
        bg = self.addColorBox(x, y, height, width, "#3a3a3a")
        elements.append(bg)

        # Draw green (elite) section
        elite_width = int(width * (count / 100))
        elite_bar = self.addColorBox(x, y, height, elite_width, "#00aa00")
        elements.append(elite_bar)

        # Draw red (non-elite) section
        nonelite_width = width - elite_width
        if nonelite_width > 0:
            nonelite_bar = self.addColorBox(
                x + elite_width, y, height, nonelite_width, "#aa0000"
            )
            elements.append(nonelite_bar)
        return elements

    def createSubGump(
        self, width, height, position="bottom", withStatus=False, alwaysVisible=True
    ):
        gump = Gump(width, height, withStatus=withStatus)
        self._setSubGumpPosition(gump.gump, width, height, position)
        API.AddGump(gump.gump)
        self.subGumps.append((gump, position, alwaysVisible))
        return gump

    def setStatus(self, text, hue=996):
        if self.withStatus:
            self.statusLabel.Text = text
            if hue:
                self.statusLabel.Hue = hue

    def onClick(self, cb, startText=None, endText=None):
        def wrapped():
            if startText:
                self.setStatus(startText)
            cb()
            if endText:
                self.setStatus(endText)

        return wrapped

    def setActiveTab(self, name):
        if name not in self.tabGumps:
            return
        for subGumps, _, alwaysVisible in self.subGumps:
            if not alwaysVisible:
                subGumps.gump.IsVisible = False
        tabGump = self.tabGumps[name]
        tabGump.gump.IsVisible = True

    def addTabButton(
        self,
        name,
        iconType,
        gumpWidth,
        callback=None,
        yOffset=45,
        withStatus=False,
        label="",
        isDarkMode=False,
    ):
        y = 10 + len(self.tabGumps) * yOffset
        x = 0

        def onClick():
            self.setActiveTab(name)
            if callback:
                callback()

        btn = self.addButton(
            label, x + 5, y, iconType, self.onClick(onClick), isDarkMode
        )
        self.buttons.append(btn)
        tabGump = self.createSubGump(gumpWidth, self.height, "right", withStatus, False)
        tabGump.gump.IsVisible = False
        self.tabGumps[name] = tabGump
        return tabGump

    def addColorBox(self, x, y, height, width, colorHex=Color.defaultBlack, opacity=1):
        colorBox = API.CreateGumpColorBox(opacity, colorHex)
        colorBox.SetX(x)
        colorBox.SetY(y)
        colorBox.SetWidth(width)
        colorBox.SetHeight(height)
        self.gump.Add(colorBox)
        return colorBox

    def addCheckbox(self, label, x, y, isChecked, callback, hue=996):
        checkbox = API.CreateGumpCheckbox(label, hue, isChecked)
        checkbox.SetX(x)
        checkbox.SetY(y)
        if callback:
            API.AddControlOnClick(checkbox, callback)
        self.gump.Add(checkbox)
        return checkbox

    def addButton(self, label, x, y, type, callback=None, isDarkMode=False):
        btnDef = Gump.buttonTypes.get(type, Gump.buttonTypes["default"])
        btn = API.CreateGumpButton(
            "", 996, btnDef["normal"], btnDef["pressed"], btnDef["hover"]
        )
        btn.SetX(x)
        btn.SetY(y)
        API.AddControlOnClick(btn, callback)
        self.gump.Add(btn)
        if type == "default":
            color = Color.defaultBlack
            if isDarkMode:
                color = Color.defaultWhite
            labelObj = self.addTtfLabel(
                label, x, y, 63, 23, 12, color, "center", callback
            )
        else:
            labelObj = API.CreateGumpLabel(label)
            labelObj.SetY(y)
            labelObj.SetX(50)
        API.AddControlOnClick(labelObj, callback)
        self.gump.Add(labelObj)
        return btn

    def addTtfLabel(
        self, label, x, y, width, height, fontSize, fontColorHex, position, callback
    ):
        ttfLabel = API.CreateGumpTTFLabel(
            label, fontSize, fontColorHex, maxWidth=width, aligned=position
        )
        centerY = y + int(height / 2) - 6
        ttfLabel.SetX(x)
        ttfLabel.SetY(centerY)
        API.AddControlOnClick(ttfLabel, self.onClick(callback))
        self.gump.Add(ttfLabel)
        return ttfLabel

    def addLabel(self, text, x, y, hue=None):
        label = API.CreateGumpLabel(text)
        label.SetX(x)
        label.SetY(y)
        if hue:
            label.Hue = hue
        self.gump.Add(label)
        return label

    def addSkillTextBox(
        self, defaultValue, x, y, minValue=0, maxValue=120, width=60, height=24
    ):
        clampedValue = max(minValue, min(maxValue, Decimal(defaultValue)))
        borderColor = "".join(Color.defaultWhite)
        borders = []
        for bx, by, bw, bh in [
            (x - 2, y - 2, width + 4, 2),
            (x - 2, y + height, width + 4, 2),
            (x - 2, y, 2, height),
            (x + width, y, 2, height),
        ]:
            border = API.CreateGumpColorBox(1, borderColor)
            border.SetX(bx)
            border.SetY(by)
            border.SetWidth(bw)
            border.SetHeight(bh)
            self.gump.Add(border)
            borders.append(border)
        textbox = API.CreateGumpTextBox(str(clampedValue), width, height, False)
        textbox.SetX(x)
        textbox.SetY(y)
        self.gump.Add(textbox)
        self.skillTextBoxes.append((textbox, minValue, maxValue, borders))
        return textbox

    def checkValidateForm(self):
        for skillTextBox, minValue, maxValue, borders in self.skillTextBoxes:
            isValidated = self._getValidatedNumber(skillTextBox, minValue, maxValue)
            color = Color.defaultWhite if isValidated else Color.defaultRed
            hue = Color.convertFromHexToHue(color)
            for border in borders:
                border.Hue = hue
            if not isValidated:
                return False
        return True

    def _getValidatedNumber(self, textbox, minValue, maxValue):
        try:
            if not textbox.Text:
                return False
            val = Decimal(textbox.Text)
            return minValue <= val <= maxValue
        except ValueError:
            return False

    def _checkEvents(self):
        API.ProcessCallbacks()
        while self.pendingCallbacks:
            cb = self.pendingCallbacks.pop(0)
            cb()

    def _setBackground(self):
        if not self.bg:
            self.bg = API.CreateGumpColorBox(0.75, Color.defaultBlack)
            self.gump.Add(self.bg)
        self.bg.SetWidth(self.width - 10)
        self.bg.SetHeight(self.height - 10)
        self.bg.SetX(0)
        self.bg.SetY(0)

    def _setBorders(
        self,
        x,
        y,
        width,
        height,
        frameColor=Color.defaultBorder,
        thickness=5,
        inside=False,
    ):
        positions = (
            [
                (x, y, width, thickness),
                (x, y + height - thickness, width, thickness),
                (x, y, thickness, height),
                (x + width - thickness, y, thickness, height),
            ]
            if inside
            else [
                (-thickness, -thickness, width, thickness),
                (-thickness, height - thickness * 2, width, thickness),
                (-thickness, -thickness, thickness, height),
                (width - thickness * 2, -thickness, thickness, height),
            ]
        )
        borders = []
        for bx, by, bw, bh in positions:
            border = API.CreateGumpColorBox(1, frameColor)
            border.SetX(bx)
            border.SetY(by)
            border.SetWidth(bw)
            border.SetHeight(bh)
            self.gump.Add(border)
            borders.append(border)
        return borders

    def _setSubGumpPosition(self, gump, width, height, position):
        gx, gy = self.gump.GetX(), self.gump.GetY()
        if position == "bottom":
            gump.SetX(gx)
            gump.SetY(gy + self.height)
        elif position == "top":
            gump.SetX(gx)
            gump.SetY(gy - height)
        elif position == "center":
            gump.SetX(gx + self.width // 2 - width // 2)
            gump.SetY(gy + self.height // 2 - height // 2)
        elif position == "left":
            gump.SetX(gx - width)
            gump.SetY(gy)
        elif position == "right":
            gump.SetX(gx + self.width)
            gump.SetY(gy)


# =========== End of _Utils\Gump.py ============#

# =========== Start of _Skills\_Music.py ============#


class Music:
    instrumentIds = [3740, 3741, 3762, 3763]

    @staticmethod
    def validate():
        errors = []
        instruments = Music._findInstruments()
        if len(instruments) == 0:
            errors.append("Music - Missing instruments")
        return errors

    @staticmethod
    def _findInstruments():
        instruments = []
        for instrumentId in Music.instrumentIds:
            items = Util.findTypeAll(API.Backpack, instrumentId)
            if len(items) > 0:
                instruments.extend(items)
        return instruments


# =========== End of _Skills\_Music.py ============#

# =========== Start of _Skills\Peacemaking.py ============#


class Peacemaking(Music):
    def __init__(self, running=None, skillCap=None):
        self.running = running
        self.skillCap = skillCap or API.GetSkill("Peacemaking").Cap
        self.instruments = self._findInstruments()
        self.skillName = "Peacemaking"
        self._done = False
        API.SetSkillLock(self.skillName, "up")

    def trainOnce(self):
        errors = Music.validate()
        if errors:
            Util.error(f"{self.skillName} - Missing instruments")
        self.use(API.Player.Serial)
        API.Pause(6)

    def train(self, calculateSkillLabels=None):
        if not self.running() or self._done:
            return True
        if Util.getSkillInfo(self.skillName)["value"] >= self.skillCap:
            self._done = True
            return True
        self.trainOnce()
        if calculateSkillLabels:
            calculateSkillLabels()
        return False

    def use(self, targetSerial):
        API.ClearJournal()
        self.instruments = self._findInstruments()
        API.UseSkill(self.skillName)
        API.Pause(0.25)
        if API.InJournalAny(
            ["You must wait a few moments to use another skill.", "$You must wait(.*)"]
        ):
            API.Pause(0.1)
            return self.use(targetSerial)
        if API.InJournalAny(
            ["What instrument shall you play?", "$What instrument(.*)"]
        ):
            API.WaitForTarget("any", 2)
            API.Target(self.instruments[0].Serial)
        API.WaitForTarget("any", 2)
        API.Target(targetSerial)
        API.CreateCooldownBar(6, "Peacemaking cooldown", 906)


# =========== End of _Skills\Peacemaking.py ============#

# =========== Start of _Utils\Secret.py ============#


class Secret:
    @staticmethod
    def loadEnv(path=LegionPath.createPath("\\.env")):
        if not os.path.exists(path):
            print(f"Warning: {path} file not found")
            return
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()


# =========== End of _Utils\Secret.py ============#

# =========== Start of _Utils\Notification.py ============#


class Notification:
    def __init__(self):
        Secret().loadEnv()

    def sendNotification(self, message):
        url = os.environ.get("NTFY_URL")
        username = os.environ.get("NTFY_USER")
        password = os.environ.get("NTFY_PASS")
        data = message.encode("utf-8")
        credentials = f"{username}:{password}"
        b64_credentials = b64encode(credentials.encode("utf-8")).decode("utf-8")

        req = urllib.request.Request(url, data=data)
        req.add_header("Authorization", f"Basic {b64_credentials}")
        req.add_header("Content-Type", "text/plain")

        try:
            with urllib.request.urlopen(req) as response:
                print(f"Notification sent. Status: {response.status}")
        except Exception as e:
            print(f"Failed to send notification: {e}")


# =========== End of _Utils\Notification.py ============#

# =========== Start of .\Sea\fishing.py ============#


class Fishing:
    offsets = [
        (-3, -3),
        (3, -3),
        (3, 3),
        (-3, 3),
    ]
    fishIds = [
        0x09CF,
        0x09CE,
        0x09CC,
        0x09CD,
        0x09CE,
        0x09CC,
        0x4306,
        0x09CD,
        0x44C6,
        0x4303,
        0x09CF,
        0x4302,
        0x44C4,
        0x4307,
        0x44C3,
        0x4306,
        0x44C4,
        0x4302,
        0x44C5,
        0x4307,
        0x4303,
        0x44C6,
        0x09CC,
        0x09CD,
        0x09CE,
    ]
    shoeIds = [0x170F, 0x170D, 0x1711, 0x170C, 0x170E, 0x1712, 0x170B, 0x1710]
    fishSteakIds = [0x097B, 0x097A]

    bigFishIds = [17158, 17159, 17156, 17157]

    def __init__(self):
        self.fishingPoleSerial = self._findItem(0x0DC0)
        self.daggerSerial = self._findItem(0x0F52)
        self.magic = Magic()
        self.lootedCorpseSerials = []
        self._validate()
        self.peacemaking = Peacemaking()
        self.peaceTimer = time.time()
        self._running = True
        self.statLabels = []
        self.lootLabels = []

        self.notification = Notification()
        self.lastNotification = time.time()
        self.notificationInterval = 3600

        self.stats = OrderedDict()
        self.stats["cast"] = {"label": "Total Casts", "count": 0, "session": 0}
        self.stats["spot"] = {"label": "Empty Spots", "count": 0, "session": 0}
        self.stats["boots"] = {"label": "Boots Pulled Up", "count": 0, "session": 0}
        self.stats["fish"] = {"label": "Fish Caught", "count": 0, "session": 0}
        self.stats["specialFish"] = {
            "label": "Special Fish Caught",
            "count": 0,
            "session": 0,
        }
        self.stats["seaSerpent"] = {
            "label": "Sea Serpents Caught",
            "count": 0,
            "session": 0,
        }
        self.stats["whitePearl"] = {
            "label": "White Pearls Collected",
            "count": 0,
            "session": 0,
        }
        self.stats["delicateScales"] = {
            "label": "Delicate Scales Gathered",
            "count": 0,
            "session": 0,
        }

        self.loots = OrderedDict()
        self.loots["gold"] = {
            "label": "Gold Looted",
            "count": 0,
            "session": 0,
            "graphic": 3821,
        }
        # self.loots["map"] = {
        #     "label": "Treasure Maps Found",
        #     "count": 0,
        #     "session": 0,
        #     "graphic": 3530,
        # }
        # self.loots["fishingNet"] = {
        #     "label": "Fishing Nets Retrieved",
        #     "count": 0,
        #     "session": 0,
        #     "graphic": 5355,
        # }
        self.loots["sos"] = {
            "label": "SOS Bottles Collected",
            "count": 0,
            "session": 0,
            "graphic": 41740,
        }
        self.loots["normalSos"] = {
            "label": "SOS Discovered",
            "count": 0,
            "session": 0,
            "graphic": 5358,
            "hue": 0,
        }
        self.loots["ancientSos"] = {
            "label": "Ancient SOS Discovered",
            "count": 0,
            "session": 0,
            "graphic": 5358,
            "hue": 1153,
        }

        self.gumpHeight = 100 + 15 * (len(self.stats) + len(self.loots))
        self.gumpWidth = 350
        self.gump = Gump(self.gumpWidth, self.gumpHeight, self._onClose)

        self.offsetIndex = 0
        self.subStep = 0
        self.currentOffset = None

        playerName = Util.getPlayerName()
        self.statsFile = f"{playerName}_fishing_stats.json"
        self._loadStats()

    def main(self):
        self._equipFishingPole()
        self._showGump()

    def tick(self):
        self._updateStatLabels()
        self._saveStats()
        self._step()

    def _loadStats(self):
        saved = {}
        if os.path.exists(self.statsFile):
            with open(self.statsFile, "r") as f:
                saved = json.load(f)
        for key, statData in self.stats.items():
            statData["count"] = saved.get(key, {}).get("count", 0)
        for key, lootData in self.loots.items():
            lootData["count"] = saved.get(key, {}).get("count", 0)
        if not os.path.exists(self.statsFile):
            self._saveStats()

    def _saveStats(self):
        data = {}
        for key, val in self.stats.items():
            data[key] = {"count": val["count"]}
        for key, val in self.loots.items():
            data[key] = {"count": val["count"]}
        with open(self.statsFile, "w") as f:
            json.dump(data, f)

    def _step(self):
        if self.subStep == 2:
            for _ in range(12):
                API.Msg("forward one")
                API.Pause(2)
            self.offsetIndex = 0
            self.currentOffset = None
            self.subStep = 0
            return

        if self.currentOffset is None or self.subStep == 0:
            if self.offsetIndex >= len(Fishing.offsets):
                self.subStep = 2
                return
            self.currentOffset = Fishing.offsets[self.offsetIndex]
            self.offsetIndex += 1
            self.subStep = 1

        if self.subStep == 1:
            xOffset, yOffset = self.currentOffset
            self._cutAndDropFish()
            actions = self._fish(xOffset, yOffset)

            if "Enemy" in actions:
                self._fightEnemy()
            # if "Boots" in actions:
            #     self._dropBoots()
            if "Fish" in actions:
                self._cutAndDropFish()
            if "Eat" in actions:
                self._eatSpecialFish()
            if "Empty" in actions:
                self.currentOffset = None
                self.subStep = 0
                return

    def _showGump(self):
        tabTotalX = self.gumpWidth - 80
        tabSessionX = self.gumpWidth - 160

        x = 10
        y = 10
        self.gump.addLabel("Current", tabSessionX, y)
        self.gump.addLabel("Total", tabTotalX, y)
        y += 15
        self.gump.addLabel("Stats:", x, y, 80)
        y += 15
        for name, statData in self.stats.items():
            self.gump.addLabel(f"{statData['label']}:", x, y)
            countLabel = self.gump.addLabel(str(statData["session"]), tabSessionX, y)
            self.statLabels.append((name, countLabel, "session"))
            countLabel = self.gump.addLabel(str(statData["count"]), tabTotalX, y)
            self.statLabels.append((name, countLabel, "count"))
            y += 15

        y += 5
        self.gump.addLabel("Loot:", x, y, 80)
        y += 15
        for name, lootData in self.loots.items():
            self.gump.addLabel(f"{lootData['label']}:", x, y)
            countLabel = self.gump.addLabel(str(lootData["session"]), tabSessionX, y)
            self.lootLabels.append((name, countLabel, "session"))
            countLabel = self.gump.addLabel(str(lootData["count"]), tabTotalX, y)
            self.lootLabels.append((name, countLabel, "count"))
            y += 15

        self.gump.create()

    def _updateStatLabels(self):
        API.SysMsg("UPDATE STAT LABELS")
        for name, countLabel, type in self.statLabels:
            count = self.stats[name][type]
            # countLabel.Text = str(count)
        for name, countLabel, type in self.lootLabels:
            count = self.loots[name][type]
            # countLabel.Text = str(count)
            API.SysMsg("UPDATE STAT LABELS - DONE")

    def _onClose(self):
        if not self._running:
            return
        self._running = False
        if self.gump:
            for subGump in self.gump.subGumps:
                subGump.destroy()
            self.gump.destroy()
            self.gump = None
        API.Stop()

    def _cast(self, spellName, targetSerial=None):
        API.ClearJournal()
        API.CancelTarget()
        retries = 3
        for attempt in range(retries):
            API.CastSpell(spellName)
            API.Pause(0.25)
            if API.InJournal("You have not yet recovered"):
                API.Pause(0.5)
                continue
            if API.InJournal("fizzles."):
                API.SysMsg(f"{spellName} fizzled. Retrying...", 33)
                API.Pause(0.5)
                continue
            if targetSerial:
                if API.WaitForTarget("any", 5):
                    API.Target(targetSerial)
                    API.Pause(0.75)
            return
        API.SysMsg(f"Failed to cast {spellName} after {retries} attempts", 33)

    def _fightEnemy(self):
        enemies = Util.scanEnemies()
        if len(enemies) > 0:
            self.gump.setStatus("Fighting...")
        for enemy in enemies:
            self._killEnemy(enemy)
        self._lootCorpses()
        self._autoHeal(0, 0)

    def _lootCorpses(self):
        corpses = Util.findCorpses()
        if len(corpses) == 0:
            self.lootedCorpseSerials.clear()
            return
        corpseSerials = []
        for corpse in corpses:
            corpseSerials.append(corpse.Serial)
        self.gump.setStatus("Looting...")
        for corpseSerial in corpseSerials:
            if corpseSerial in self.lootedCorpseSerials:
                continue
            corpse = API.FindItem(corpseSerial)
            Util.openContainer(corpse)
            items = Util.itemsInContainer(corpseSerial)
            for item in items:
                for loot in self.loots:
                    lootId = self.loots[loot]["graphic"]
                    if item.Graphic == lootId:
                        if item.Graphic == 3821:
                            self.loots[loot]["count"] += item.Amount
                            self.loots[loot]["session"] += item.Amount
                        else:
                            self.loots[loot]["count"] += 1
                            self.loots[loot]["session"] += 1
                        Util.moveItem(item.Serial, API.Backpack)
            self._openSoses()
            self.lootedCorpseSerials.append(corpseSerial)

    def _openSoses(self):
        startingSosCount = len(Util.findTypeAll(API.Backpack, 5358, 0))
        startingAncientSosCount = len(Util.findTypeAll(API.Backpack, 5358, 1153))
        for sosBottle in Util.findTypeAll(API.Backpack, 41740):
            API.Pause(0.25)
            Util.useObject(sosBottle.Serial)
            API.Pause(1)
            newSosCount = len(Util.findTypeAll(API.Backpack, 5358, 0))
            if newSosCount > startingSosCount:
                self.loots["normalSos"]["count"] += 1
                self.loots["normalSos"]["session"] += 1
                startingSosCount += 1
            newAncientSosCount = len(Util.findTypeAll(API.Backpack, 5358, 1153))
            if newAncientSosCount > startingAncientSosCount:
                self.loots["ancientSos"]["count"] += 1
                self.loots["ancientSos"]["session"] += 1
                startingAncientSosCount += 1

    def _autoHeal(self, offsetGreaterHeal=40, offsetHeal=20):
        while API.BuffExists("Poisoned"):
            self._cast("Cure", API.Player.Serial)
        hpMissing = API.Player.HitsMax - API.Player.Hits
        while hpMissing > offsetHeal:
            if hpMissing >= offsetGreaterHeal:
                self._cast("Greater Heal", API.Player.Serial)
            elif hpMissing >= offsetHeal:
                self._cast("Heal", API.Player.Serial)
            hpMissing = API.Player.HitsMax - API.Player.Hits

    def _killEnemy(self, enemy):
        while API.FindMobile(enemy.Serial):
            now = time.time()
            if enemy.InWarMode and now - self.peaceTimer > 6:
                self.peaceTimer = time.time()
                self._peace(enemy)
            self._autoHeal()
            self._cast("Energy Bolt", enemy.Serial)

    def _peace(self, enemy):
        if Util.getSkillInfo("Peacemaking")["value"] < 100:
            return
        self.peacemaking.use(enemy.Serial)

    def _dropBoots(self):
        goat = self._findGoat()
        for shoeId in Fishing.shoeIds:
            shoes = Util.findTypeAll(API.Backpack, shoeId)
            for shoe in shoes:
                Util.moveItem(shoe.Serial, goat.Serial)

    def _eatSpecialFish(self):
        specialFishes = Util.findTypeAll(API.Backpack, 0x0DD6)
        for specialFish in specialFishes:
            API.UseObject(specialFish.Serial)
            API.Pause(1)

    def _cutAndDropFish(self):
        weightDiff = API.Player.WeightMax - API.Player.Weight
        if weightDiff > 35:
            return
        for fishId in Fishing.fishIds:
            fishes = Util.findTypeAll(API.Backpack, fishId)
            for fish in fishes:
                Util.useObjectWithTarget(self.daggerSerial)
                API.Target(fish.Serial)
                API.Pause(0.25)
        for fishSteakId in Fishing.fishSteakIds:
            fishSteakWorld = Util.findTypeWorld(fishSteakId)
            fishSteaks = Util.findTypeAll(API.Backpack, fishSteakId)
            for fishSteak in fishSteaks:
                if fishSteakWorld:
                    Util.moveItem(fishSteak.Serial, fishSteakWorld.Serial)
                else:
                    Util.moveItemOffset(fishSteak.Serial, 1, 1)
                    fishSteakWorld = Util.findTypeWorld(fishSteakId)
        for bigFishId in Fishing.bigFishIds:
            bigFishes = Util.findTypeAll(API.Backpack, bigFishId)
            for bigFish in bigFishes:
                Util.moveItemOffset(bigFish.Serial, -1, 1)

    def _validate(self):
        hasMagery = Util.getSkillInfo("Magery")["value"] > 0
        if not hasMagery:
            Util.error("Need magery")
        while not API.BuffExists("Protection"):
            self.magic.cast("Protection")
        # self._findGoat()

    def _findGoat(self):
        pets = API.GetAllMobiles()
        for pet in pets:
            isGoat = pet.Graphic == 209
            distance = Math.distanceBetween(API.Player, pet)
            if isGoat and pet.IsRenamable and not pet.IsHuman and distance < 2:
                API.HeadMsg("Goat Located", pet.Serial)
                return pet
        Util.error("Missing goat")

    def _fish(self, xOffset, yOffset):
        self.gump.setStatus("Fishing...")
        API.ClearJournal()
        self._lootCorpses()
        self.stats["cast"]["count"] += 1
        self.stats["cast"]["session"] += 1
        Util.useObjectWithTarget(self.fishingPoleSerial)
        API.TargetLandRel(xOffset, yOffset)
        API.CreateCooldownBar(10, "Fishing...", 88)
        actions = self._scanJournal()
        return actions

    def _scanJournal(self):
        while True:
            res = []
            if API.InJournalAny(
                [
                    "Uh oh! That doesn't look like a fish!",
                ]
            ):
                self.stats["seaSerpent"]["count"] += 1
                self.stats["seaSerpent"]["session"] += 1
                res.append("Enemy")
            if API.InJournalAny(
                [
                    "You pull out an item : uncommon shiner",
                    "You pull out an item : brook trout",
                    "You pull out an item : bluegill sunfish",
                    "You pull out an item : smallmouth bass",
                    "You pull out an item : green catfish",
                    "You pull out an item : kokanee salmon",
                    "You pull out an item : walleye",
                    "You pull out an item : rainbow trout",
                    "You pull out an item : pike",
                    "You pull out an item : pumpkinseed sunfish",
                    "You pull out an item : yellow perch",
                    "You pull out an item : redbelly bream",
                    "You pull out an item : bonefish",
                    "You pull out an item : tarpon",
                    "You pull out an item : blue grouper",
                    "You pull out an item : cape cod",
                    "You pull out an item : yellowfin tuna",
                    "You pull out an item : gray snapper",
                    "You pull out an item : red drum",
                    "You pull out an item : shad",
                    "You pull out an item : captain snook",
                    "You pull out an item : mahi-mahi",
                    "You pull out an item : red grouper",
                    "You pull out an item : bonito",
                    "You pull out an item : cobia",
                    "You pull out an item : amberjack",
                    "You pull out an item : haddock",
                    "You pull out an item : bluefish",
                    "You pull out an item : red snook",
                    "You pull out an item : black seabass",
                    "You pull out an item : grim cisco",
                    "You pull out an item : infernal tuna",
                    "You pull out an item : lurker fish",
                    "You pull out an item : orc bass",
                    "You pull out an item : snaggletooth bass",
                    "You pull out an item : tormented pike",
                    "You pull out an item : darkfish",
                    "You pull out an item : drake fish",
                    "Your fishing pole bends as you pull a big fish from the depths!",
                    "Your fishing pole bends as you pull a rare fish from the depths!",
                    "$Your fishing pole bends as you pull(.*)!",
                ]
            ):
                self.stats["fish"]["count"] += 1
                self.stats["fish"]["session"] += 1
                res.append("Fish")
            if API.InJournalAny(
                [
                    "You pull out an item : a mess of small fish",
                ]
            ):
                self.stats["specialFish"]["count"] += 1
                self.stats["specialFish"]["session"] += 1
                res.append("Eat")
            if API.InJournalAny(
                [
                    "You pull out an item : thigh boots",
                    "You pull out an item : shoes",
                    "You pull out an item : boots",
                    "You pull out an item : sandals",
                ]
            ):
                self.stats["boots"]["count"] += 1
                self.stats["boots"]["session"] += 1
                res.append("Boots")
            if API.InJournalAny(
                [
                    "You fish a while, but fail to catch anything",
                ]
            ):
                res.append("Fail")
            if API.InJournalAny(
                [
                    "The fish don't seem to be biting here",
                    "You need to be closer to the water to fish!",
                ]
            ):
                self.stats["spot"]["count"] += 1
                self.stats["spot"]["session"] += 1
                res.append("Empty")
            if API.InJournalAny(["You have found a white pearl!"]):
                self.stats["whitePearl"]["count"] += 1
                self.stats["whitePearl"]["session"] += 1
            if API.InJournalAny(
                [
                    "As you reel in, you notice that there is something odd tangled in the line."
                ]
            ):
                self.stats["delicateScales"]["count"] += 1
                self.stats["delicateScales"]["session"] += 1
            if len(res) > 0:
                self._updateStatLabels()
                return res
            API.Pause(0.5)

    def _findItem(self, itemId):
        API.ClearLeftHand()
        API.ClearRightHand()
        API.Pause(1)
        fishingPole = Util.findType(API.Backpack, itemId)
        if not fishingPole:
            API.SysMsg(f"No: {str(itemId)}", 33)
            API.Stop()
        return fishingPole.Serial

    def _equipFishingPole(self):
        API.EquipItem(self.fishingPoleSerial)
        API.Pause(0.25)

    def _isRunning(self):
        return self._running

    def _sendHourlyStats(self):
        lines = ["📊 Fishing Stats (Last Hour)"]
        for key, data in self.stats.items():
            lines.append(f"{data['label']}: {data['session']}")
        lines.append("\n🎁 Loot Collected:")
        for key, data in self.loots.items():
            lines.append(f"{data['label']}: {data['session']}")
        message = "\n".join(lines)
        self.notification.sendNotification(message)
        for data in self.stats.values():
            data["session"] = 0
        for data in self.loots.values():
            data["session"] = 0


fishing = Fishing()
try:
    fishing.main()
    while fishing._isRunning():
        now = time.time()
        fishing.gump.tick()
        fishing.gump.tickSubGumps()
        fishing.tick()
        if now - fishing.lastNotification >= fishing.notificationInterval:
            fishing._sendHourlyStats()
            fishing.lastNotification = now
        API.Pause(0.1)
except BaseException as e:
    Error.logError(e, "Fishing")
    fishing._onClose()
# =========== End of .\Sea\fishing.py ============#
