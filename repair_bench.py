RepairBenchSerial = 0x400D3B76 # <- west
RepairBenchGumpID = 1917797751
RepairDeedGumpID = 949095101
AddChargeButtonID = 1

ScrollItemId = 0x0EF3 # Blank Scroll
ToolItemID = 0x0FBB # 0xF9D Sewing Kit, 0x1EB8 Tinker Tool Kit, 0x13E3 BS hammer, 0x0FBB tongs

def GetItemsInContainer(ContainerSerial):
    ContainerCount = 0
    ContainerList = ContainerSerial.Contains
    
    if len(ContainerList) > 0 :
        for Obj in ContainerList:
            if not Obj.IsContainer:
                ContainerCount += 1
            else:
                PartialCount = (GetItemsInContainer(Obj) + 1) #need to add the bag itself
                ContainerCount += PartialCount
    return ContainerCount
        
AvailableSpace = 125 - GetItemsInContainer(Player.Backpack) 
BlankScroll = Items.FindByID(ScrollItemId,0,Player.Backpack.Serial,1,False)
Tool = Items.FindByID(ToolItemID,0, Player.Backpack.Serial,1,False)

CycleCount = min(AvailableSpace,BlankScroll.Amount)

if BlankScroll != None and Tool != None:
    for x in range(CycleCount):
        Items.UseItem(Tool)
        Gumps.WaitForGump(RepairDeedGumpID,10000)
        Gumps.SendAction(RepairDeedGumpID,42)
        Target.WaitForTarget(10000,False)
        Target.TargetExecute(BlankScroll)
        Gumps.WaitForGump(RepairDeedGumpID,10000)
        Gumps.CloseGump(RepairDeedGumpID)
        Misc.Pause(600)
    
    Items.UseItem(RepairBenchSerial)
    Gumps.WaitForGump(RepairBenchGumpID,10000)
    Gumps.SendAction(RepairBenchGumpID,AddChargeButtonID)
    Target.WaitForTarget(10000,False)
    Target.TargetExecute(Player.Backpack)
    Gumps.WaitForGump(RepairBenchGumpID,10000)
    Gumps.CloseGump(RepairBenchGumpID)
    
else:
    if BlankScroll == None:
        Player.HeadMessage(240,"No Blank Scroll available")
    if Tool == None:
        Player.HeadMessage(240,"No Tool available")