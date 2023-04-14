# not my script.
# see: https://discord.com/channels/221645501806804993/1077747436329644092/1077930384655921163

WOOD_LOGS = 0x1BDD
AXE_SERIAL = 0x404CBB89

# Determine your weight carrying capacity, and set thresholds relative to it.
max_weight = Player.MaxWeight
start_chopping_logs_weight = max_weight - 30
stop_chopping_trees_weight = max_weight - 10

# Equip your axe if not already equipped.
axe_serial = Player.GetItemOnLayer('LeftHand')
if not axe_serial:
    Misc.SendMessage('No axe found!')
    axe_serial = AXE_SERIAL
    Player.EquipItem(axe_serial)
    Misc.Pause(600)

# Chop trees as you run up against them, until you are too heavy.
while True:
    
    Journal.Clear()
    Target.TargetResource(AXE_SERIAL,"wood")
    Misc.Pause(200)
    
    # If getting heavy, chop up the logs.
    if Player.Weight >= start_chopping_logs_weight:
        Misc.SendMessage("Heavy, chop logs....")

        log = Items.FindByID(WOOD_LOGS, -1, Player.Backpack.Serial) 
        while log != None:
            Items.UseItem(axe_serial)
            Target.WaitForTarget(5000, False)
            Target.TargetExecute(log)
            Misc.Pause(1000)
            log = Items.FindByID(WOOD_LOGS, -1, Player.Backpack.Serial)
            
            Organizer.FStop()
            Misc.Pause(600)
            
            Organizer.ChangeList('gathering')
            Organizer.FStart()
            Misc.Pause(600)
            
            while Organizer.Status():
                Player.HeadMessage(33, 'Organizing')
                Misc.Pause(600)
                
            Misc.Pause(600)
    # Stop chopping trees when we can't carry more.
    if Player.Weight >= stop_chopping_trees_weight:
        Misc.SendMessage("Too heavy....  Stop")
        break