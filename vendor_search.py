item = Items.FindBySerial(Target.PromptTarget('What do you want to search?', 62))

from System.Collections.Generic import List
from System import Int32

vs_gump = 1005351445
Misc.UseContextMenu(Player.Serial, 'Vendor Search', 5000)
Gumps.WaitForGump(vs_gump, 3000)
Gumps.SendAction(vs_gump, 2)  # reset
Gumps.WaitForGump(vs_gump, 3000)
Gumps.SendAdvancedAction(vs_gump, 1, List[Int32]([1]), List[str]([item.Name]))
Gumps.WaitForGump(vs_gump, 3000)
if Gumps.HasGump(vs_gump):
    Gumps.CloseGump(vs_gump)