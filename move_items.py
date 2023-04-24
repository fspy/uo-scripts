# move all of selected to destination container
import sys
from AutoComplete import *

source_item = Target.PromptTarget('What do you want to move?', 96)
destination_container = Target.PromptTarget('Where do you want it?', 150)

if not (source_item and destination_container):
    Misc.SendMessage("Oh no! Something's off... bailing", 33)
    sys.exit()

Misc.SendMessage('Okay, moving stuff!', 62)

item = Items.FindBySerial(source_item)
for i in Items.FindAllByID(item.ItemID, item.Hue, -1, -1):
    Items.Move(i, destination_container, -1)
    Misc.Pause(625)

Misc.SendMessage("I think it's done!", 62)