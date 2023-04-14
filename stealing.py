# -----------------------------------------------
# Credits: McPaperstax
# Info: Training script prompts target for locked/secure container in player home. Finds first item of appropriate weight to steal.
# -----------------------------------------------

hue = 177

# Delay for Journal Clear / Search in ms. Without delay Journal Search does not function properly.
delay = 250


def FindSteal( container, weight):    
#    Defines container by Serial param
#    finds next Item by ideal weight param
#    Returns foundItem or -1 if no item found
    
    container =  Items.FindBySerial(container)
    Misc.SendMessage('Container Name: ' + container.Name, hue)
    Misc.SendMessage('Container Valid: ' + str(container.IsContainer), hue)
    
    foundItem = next( ( item for item in container.Contains if ( item.Weight == weight ) ), None )
    
    if foundItem != None:
        Player.HeadMessage(hue,'Found '+foundItem.Name + ' weighing ' + str(foundItem.Weight) + ' stones.')
        return foundItem
    else:
        Player.HeadMessage(hue,'No item found to steal.')
        return -1


def StealItem ( container, item ):
#    Clears Journal and attempts steal
#    Waits and exits to main loop on fail
#    Returns item to container on success
    Journal.Clear()
    Misc.Pause(delay)
    
    Player.UseSkill('Stealing')
    Target.WaitForTarget(2000,True)
    Target.TargetExecute(item)
    Misc.Pause(delay)
    
    if Journal.SearchByName('You fail to steal the item.', 'System'):
        Misc.SendMessage('Steal Fail.', hue)
        #Steal fail pause and retry
    elif Journal.SearchByName('You successfully steal the item.', 'System'):
        Misc.SendMessage('Steal Success.', hue)
        #Steal succeed return item to container
        Items.Move(item.Serial, container, 0)
        
    Misc.Pause(10000)
    Misc.SendMessage('Next Attempt',hue)
        
# -----------------------------------
# Main Script Execution Begins Here
# -----------------------------------

container = Target.PromptTarget("Select container to train stealing.",hue)
Misc.SendMessage(container, hue)


while Player.GetRealSkillValue('Stealing') < Player.GetSkillCap('Stealing'):
    
    currentSkill = Player.GetRealSkillValue('Stealing')
    
    if currentSkill < 40:
        Player.HeadMessage('Train or Soulstone stealing skill to 40 or higher.' ,hue)
    elif currentSkill < 50:
        item = FindSteal(container, 4)
    elif currentSkill < 60:
        item = FindSteal(container, 5)
    elif currentSkill < 70:
        item = FindSteal(container, 6)
    elif currentSkill < 80:
        item = FindSteal(container, 7)
    elif currentSkill < 90:
        item = FindSteal(container, 8)
    elif currentSkill < 100:
        item = FindSteal(container, 9)
    elif currentSkill < 110:
        item = FindSteal(container, 10)
    else:
        item = FindSteal(container, 11)
   
    if item != -1:
        StealItem( container, item )
    else:
        break
        
Misc.SendMessage('Stealing script has stopped running.', hue)