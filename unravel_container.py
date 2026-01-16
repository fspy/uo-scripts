import API

API.HeadMsg("target container", API.Player)
target = API.FindItem(API.RequestTarget())

if not target:
    API.HeadMsg("no target?", API.Player)
    API.Stop()

API.UseSkill("Imbuing")

if not API.WaitForGump(0x65290B89):
    API.SysMsg("imbuing gump timed out")
    API.Stop()

API.ReplyGump(10011, 0x65290B89)
API.WaitForTarget()
API.Target(target)  # pyright: ignore

if not API.WaitForGump(0xB73E81BB):
    API.SysMsg("confirmation gump timed out")
    API.Stop()

API.ReplyGump(1, 0xB73E81BB)
