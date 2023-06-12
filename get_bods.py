from AutoComplete import *

from lib.util import head_prompt

npc = head_prompt("Target BOD NPC")
npc = Mobiles.FindBySerial(npc)

Journal.Clear("an offer may be available in")
while not Journal.SearchByName("an offer may be available in", npc.Name):
    Misc.UseContextMenu(npc.Serial, "bulk order info", 5000)
    Gumps.WaitForGump(0, 5000)
    if Gumps.LastGumpTextExist('A bulk order'):
        Gumps.SendAction(Gumps.CurrentGump(), 1)
    Misc.Pause(625)
