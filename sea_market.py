ingots = Items.BackpackCount(0x1BF2,0)
stone = Items.FindByID(0xA583,0x054B,-1,24,False)
if stone:
    if ingots >= 245:
        Player.HeadMessage(33,"(Buying ammo)")
        Items.UseItem(0x4001A3B2)
        Gumps.WaitForGump(4241020643, 10000)
        Gumps.SendAction(4241020643, 13)
        Gumps.WaitForGump(1615557655, 10000)
        Gumps.SendAction(1615557655, 2)
        Misc.Pause(200)
        Items.UseItem(0x4001A3B2)
        Gumps.WaitForGump(4241020643, 10000)
        Gumps.SendAction(4241020643, 14)
        Gumps.WaitForGump(1615557655, 10000)
        Gumps.SendAction(1615557655, 2)
        Misc.Pause(200)
        Items.UseItem(0x4001A3B2)
        Gumps.WaitForGump(4241020643, 10000)
        Gumps.SendAction(4241020643, 11)
        Gumps.WaitForGump(1615557655, 10000)
        Gumps.SendAction(1615557655, 2)
        Misc.Pause(200)
        Gumps.CloseGump(4241020643)
        Player.HeadMessage(33,"(Purchase complete)")
    else:
        Player.HeadMessage(33,"(Not enough ingots)")
        Player.HeadMessage(33,"(You have {}, need 245)".format(ingots))
else:
    Player.HeadMessage(33,"(Not by the stone)")