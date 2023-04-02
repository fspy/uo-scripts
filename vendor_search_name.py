import re
from System.Collections.Generic import List
from System import Int32

def edge_cases_tip_of_iceberg(txt):
    # dont strip numbers from power/stat scrolls
    # numbers are stripped for cases such as commodities and raw materials (137 ingots)
    if 'scroll of' in txt:
        return txt
    else:
        return re.sub(r'\s*\d+\s*', '', txt)

target = Target.PromptTarget("Target the item you'd like to search!", 1151)
if target:
    item = Items.FindBySerial(target)
    name = edge_cases_tip_of_iceberg(item.Name)
    if Gumps.CurrentGump() is not 999112:
        Misc.WaitForContext(Player.Serial, 2000)
        Misc.ContextReply(Player.Serial, 1)
    Gumps.WaitForGump(999112, 2000)
    Gumps.SendAction(999112, 2) # Clear Search
    Gumps.SendAdvancedAction(999112, 1, List[Int32]([1]), List[str]([name]))
