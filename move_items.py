# move all to dest
import sys

item = Target.PromptTarget('What do you want to move?', 96)
dest = Target.PromptTarget('Where do you want it?', 150)

if not (item and dest):
    Misc.SendMessage("Oh no! Something's off... bailing", 33)
    sys.exit()

item = Items.FindBySerial(item)
Misc.SendMessage('Okay, moving stuff!', 62)
for i in Items.FindAllByID(item.ItemID, item.Hue, -1, -1):
    Items.Move(i, dest, -1)
    Misc.Pause(650)
Misc.SendMessage("I think it's done!", 62)