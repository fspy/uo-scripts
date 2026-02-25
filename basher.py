import API


while not API.Player.IsDead:
    if API.Player.IsHidden:
        API.Pause(0.1)
        continue

    abilities = list(API.CurrentAbilityNames())

    if API.BuffExists("Paralyze"):
        API.UseType(0x0E7E, container=API.Backpack, skipQueue=True)
    if not API.BuffExists("Enemy Of One") and API.Player.Mana > 20:
        API.CastSpell("Enemy of One")
        API.Pause(0.25)
    if not API.BuffExists("Consecrate") and API.Player.Mana > 12:
        API.CastSpell("Consecrate Weapon")
        API.Pause(0.25)
    if not API.BuffExists("Shield Bash") and API.Player.Mana > 35:
        API.CastSpell("Shield Bash")
        API.Pause(0.1)
    if API.BuffExists("Shield Bash") and API.Player.Mana > 20:
        ai = abilities.index("ArmorIgnore") if "ArmorIgnore" in abilities else -1
        if ai == 0 and not API.PrimaryAbilityActive():
            API.ToggleAbility("primary")
            API.Pause(0.1)
        if ai == 1 and not API.SecondaryAbilityActive():
            API.ToggleAbility("secondary")
            API.Pause(0.1)

    API.Pause(0.1)
