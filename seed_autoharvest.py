"""
Script for harvesting seeds and resources
    Run the script and WALK around your plants, range is 4 tiles.
    If the plant turns TRUE BLACK, it means succesful harvest and you can continue to other plants 
    If the plant turns GOLDEN, it means plant was out of reach during harvest, move into range of 4 tiles from plant.
    If the plant turns TRUE WHITE, it's ready to turn into DECORATIVE. Use second script in thread for this.
"""
### SETTINGS: ###
gumpWaitTimeout = 500
timeoutLoop = 200
setColorForHarvestedPlants = True # restore color by restarting whole client, lol.
harvested_plant_color = 1 # True black, plant got harvested succesfully, you can move
out_of_reach_plant_color = 2734 # Golden color, script tried to harvest plant but it was out of reach, move near
ready_to_turn_decorative_plant_color = 2060 # True white, plant is ready to turn into decorative
#-------------------------------------------------#


if True == False: from AutoComplete import *
from System.Collections.Generic import List
import re


ignore = []
reproduction_found = False
decorative_slash_found = False
no_resources_for_harvest_found = False

def has_numbers(inputString):
    return bool(re.search(r'\d', inputString))

def getPlantItemsByName(name):
    
    filter_tree = Items.Filter()
    filter_tree = Items.Filter()
    filter_tree.Name = name
    filter_tree.RangeMax = 3
    filter_tree.OnGround = True
    
    return Items.ApplyFilter(filter_tree)

if __name__ == '__main__':
    
    Misc.Resync()
    
    while True:
        plants_list_results = [getPlantItemsByName('Tree'), 
                            getPlantItemsByName('Plant'), 
                            getPlantItemsByName('Bush'),
                            getPlantItemsByName('Canes')]

        for oneResultItemsList in plants_list_results:
            for plant in oneResultItemsList:
                if not plant.Serial in ignore:
                    
                    # reset decorative plant check variables
                    reproduction_found = False
                    decorative_slash_found = False
                    no_resources_for_harvest_found = False
                    
                    # harvest only plants on same Z level, otherwise it try to open plants gump on different floors in hours
                    if plant.Position.Z != Player.Position.Z + 5:
                        # Misc.SendMessage('Plant is not on the same Z level!, skipping: ' + plant.Name)
                        Misc.Pause(timeoutLoop)
                        continue
                    
                    Misc.SendMessage('Trying to harvest: ' + plant.Name)
                    
                    Journal.Clear()
                    Gumps.ResetGump()
                    Items.UseItem(plant)
                
                    if not Gumps.WaitForGump(2847473961, gumpWaitTimeout):
                        # Plant is out of reach for harvest
                        Misc.SendMessage('Can\'t reach: ' + plant.Name + ' skipping.')
                        if setColorForHarvestedPlants:
                            Items.SetColor(plant.Serial, out_of_reach_plant_color) 
                        continue
                    
                    Gumps.WaitForGump(2847473961, gumpWaitTimeout)
                    Gumps.SendAction(2847473961, 1)
                    Gumps.WaitForGump(1726216037, gumpWaitTimeout)
                    Gumps.SendAction(1726216037, 7)
                    Gumps.WaitForGump(1726216037, gumpWaitTimeout)
                    Gumps.SendAction(1726216037, 8)
                    Gumps.WaitForGump(1726216037, gumpWaitTimeout)
                    Gumps.SendAction(1726216037, 0)
                    
                    ignore.append(plant.Serial)
                    if setColorForHarvestedPlants:
                         
                        # Check if plant is ready to turn decorative, and re-color it
                        Misc.Pause(500)
                        str_gump = Gumps.GetLineList(1726216037)
                        for one in str_gump:
                            if one:
                                
                                if one == 'Reproduction':
                                    reproduction_found = True
                                    #Misc.SendMessage('Reproduction found')
                                elif one == "/":
                                    decorative_slash_found = True
                                    #Misc.SendMessage('Decorative slash found')
                                else:
                                    no_resources_for_harvest_found = not has_numbers(one) 
                                      
                        if no_resources_for_harvest_found and reproduction_found and decorative_slash_found:
                            Misc.SendMessage('Ready to turn decorative - ' + plant.Name)  
                            Items.SetColor(plant.Serial, ready_to_turn_decorative_plant_color) 
                        else:
                            # Harvested plant, color it
                            Items.SetColor(plant.Serial, harvested_plant_color) 
                                          
        Misc.Pause(timeoutLoop)