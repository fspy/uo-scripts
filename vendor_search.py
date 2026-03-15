import API

SEARCH_GUMP = 0xF3EC8
RESULT_GUMP = 0xB9D680BB


API.HeadMsg("target item", API.Player, 185)
item = API.FindItem(API.RequestTarget(30))
if not item:
    API.HeadMsg("invalid item", API.Player, 33)
    API.Stop()


API.CloseGump(SEARCH_GUMP)
API.ContextMenu(API.Player, 1)
API.WaitForGump(SEARCH_GUMP)
API.ReplyGump(1, SEARCH_GUMP, entries=[(1, item.Name)])

API.WaitForGump(SEARCH_GUMP)
if "No items matched your search" in API.GetGumpContents(SEARCH_GUMP):
    API.HeadMsg("no items found!", API.Player, 55)

API.CloseGump(SEARCH_GUMP)
