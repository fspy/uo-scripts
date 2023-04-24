# move everything inside source to destination container
import sys
from AutoComplete import *

source = Target.PromptTarget('Move items from where?', 96)
destination = Target.PromptTarget('Where do I put them?', 150)

if not (source and destination):
    Misc.SendMessage('Did you goof something up?', 33)
    sys.exit()


def get_items(cont):
    """flattened list of a container's items"""
    items = []
    Items.WaitForContents(cont, 2000)
    for i in Items.FindBySerial(cont).Contains:
        items.append(i)
        if i.IsContainer:
            items.extend(get_items(i))
    return items


Misc.SendMessage('Okay, moving stuff!', 62)

for i in get_items(source):
    Items.Move(i, destination, 0)
    Misc.Pause(620)

Misc.SendMessage("I think it's done!", 62)