import API
from _lib.utils import Hue, get_mastery, p, toggle_mount

masteries = {
    # https://github.com/ServUO/ServUO/blob/pub57/Server/Skills.cs#L28
    # https://github.com/ServUO/ServUO/blob/pub57/Scripts/Spells/Skill%20Masteries/Core/SelectMasteryGump.cs#L42
    "Provocation": ("Inspire", "Invigorate", 23),
    "Peacemaking": ("Resilience", "Perseverance", 10),
    "Discordance": ("Tribulation", "Despair", 16),
    # Mastery isn't called Discordance...
    "Discord": ("Tribulation", "Despair", 16),
}


def cast_mastery_spell(idx):
    mastery = get_mastery()
    if mastery and masteries[mastery]:
        API.CastSpell(masteries[mastery][idx])


def switch_mastery(to):
    API.FindType(0x225A, API.Backpack, hue=0)
    if not API.Found:
        p("Book of Masteries not found!", Hue.Red)
        return

    if to == get_mastery():
        p(f"Mastery already active: {to}", Hue.Blue)
        return

    API.ContextMenu(API.Found, 0)
    if API.WaitForGump(0x6A0ECF23, 3):
        if to not in API.GetGumpContents(0x6A0ECF23):
            p(f"You don't have the {to} mastery!", Hue.Magenta)
            API.CloseGump(0x6A0ECF23)
            return
        API.ReplyGump(masteries[to][2], 0x6A0ECF23)
    else:
        p("Unable to change masteries, is it on cooldown?", Hue.Orange)


def new_spell_trigger(spell):
    reply = 101  # Healing Stone

    if spell == "Cleansing Winds":
        if API.GetSkill("Mysticism").Value < 120:
            p("Insufficient Mysticism Skill!", Hue.Magenta)
            return
        reply = 201

    API.CastSpell("Spell Trigger")
    API.WaitForGump(0xA66CB638)
    API.ReplyGump(reply, 0xA66CB638)


def use_spell_trigger():
    API.FindType(0x4079, API.Player.Backpack, hue=0)
    if API.Found:
        API.UseObject(API.Found, skipQueue=True)


def use_healing_stone():
    API.FindType(0x4078, API.Player.Backpack, hue=0)
    if API.Found:
        API.UseObject(API.Found, skipQueue=True)


def peace_self():
    API.PreTarget(API.Player)
    API.UseSkill("Peacemaking")


API.OnHotKey("SDLK_GRAVE", lambda: API.PlayScript("smart_heal.py"))
API.OnHotKey("1", lambda: API.CastSpell("Cure"))
API.OnHotKey("2", lambda: API.CastSpell("Heal"))
API.OnHotKey("3", lambda: API.CastSpell("Greater Heal"))
API.OnHotKey("4", lambda: API.CastSpell("Cleansing Winds"))
API.OnHotKey("5", lambda: API.CastSpell("Arch Cure"))
API.OnHotKey("Q", lambda: API.CastSpell("Nether Bolt"))
API.OnHotKey("W", lambda: API.CastSpell("Eagle Strike"))
API.OnHotKey("E", lambda: API.CastSpell("Bombard"))
API.OnHotKey("R", lambda: API.CastSpell("Hail Storm"))
API.OnHotKey("T", lambda: API.CastSpell("Spell Plague"))
API.OnHotKey("A", lambda: cast_mastery_spell(0))
API.OnHotKey("S", lambda: cast_mastery_spell(1))
API.OnHotKey("D", lambda: API.UseSkill("Discordance"))
API.OnHotKey("F", lambda: API.UseSkill("Provocation"))
API.OnHotKey("Z", lambda: API.CastSpell("Invisibility"))
API.OnHotKey("X", lambda: API.CastSpell("Resurrection"))
API.OnHotKey("C", lambda: API.CastSpell("Mass Dispel"))
API.OnHotKey("V", lambda: API.CastSpell("Rising Colossus"))

API.OnHotKey("Shift+SDLK_GRAVE", toggle_mount)
API.OnHotKey("Shift+1", lambda: new_spell_trigger("Cleansing Winds"))
API.OnHotKey("Shift+2", lambda: new_spell_trigger("Healing Stone"))
API.OnHotKey("Shift+3", use_spell_trigger)
API.OnHotKey("Shift+4", use_healing_stone)
API.OnHotKey("Shift+A", lambda: API.UseSkill("Peacemaking"))
API.OnHotKey("Shift+S", peace_self)

API.OnHotKey("Ctrl+SDLK_GRAVE", lambda: API.PlayScript("use_gate.py"))
API.OnHotKey("Ctrl+2", lambda: API.Msg("All Follow Me"))
API.OnHotKey("Ctrl+R", lambda: API.CastSpell("Recall"))
API.OnHotKey("Ctrl+T", lambda: API.CastSpell("Teleport"))
API.OnHotKey("Ctrl+A", lambda: switch_mastery("Peacemaking"))
API.OnHotKey("Ctrl+D", lambda: switch_mastery("Discord"))
API.OnHotKey("Ctrl+F", lambda: switch_mastery("Provocation"))
API.OnHotKey("Ctrl+G", lambda: API.CastSpell("Gate Travel"))
API.OnHotKey("Ctrl+H", lambda: API.UseSkill("Hiding"))
API.OnHotKey("Ctrl+C", lambda: API.CastSpell("Mark"))

API.OnHotKey("Alt+SDLK_GRAVE", lambda: p("go_home script"))
API.OnHotKey("Alt+1", lambda: API.CastSpell("Reactive Armor"))
API.OnHotKey("Alt+2", lambda: API.CastSpell("Magic Reflection"))
API.OnHotKey("Alt+3", lambda: API.CastSpell("Protection"))
API.OnHotKey("Alt+4", lambda: API.CastSpell("Stone Form"))

API.OnHotKey("F9", lambda: API.Msg("[ohshit"))
API.OnHotKey("F10", lambda: API.Msg("[crl"))

while not API.StopRequested:
    API.ProcessCallbacks()
    API.Pause(0.05)
