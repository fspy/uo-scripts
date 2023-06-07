axe = Player.GetItemOnLayer('LeftHand')
satchel = Items.FindByID(0xA274, -1, Player.Backpack.Serial, 1)
while Player.Weight < Player.MaxWeight:
    Target.TargetResource(axe, 'wood')
    Misc.Pause(1200)
    if Player.Weight > 400:
        print('heavy')
        logs = Items.FindAllByID(0x1BDD, -1, Player.Backpack.Serial, True)
        for l in logs:
            Items.UseItem(axe)
            Target.WaitForTarget(3000)
            Target.TargetExecute(l)
            Misc.Pause(200)
            
        if not satchel:
            continue

        wood = Items.FindAllByID(0x1BD7, -1, Player.Backpack.Serial, 0)
        for w in wood:
            Items.Move(w.Serial, satchel.Serial, 0)
            Misc.Pause(625)

print('Overweight, go dump logs!')