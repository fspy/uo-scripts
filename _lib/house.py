from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import API

# Set Permission gump ID (Co-Owner selection)
SET_PERMISSION_GUMP_ID = 0x29B6C49


def auto_coown():
    while not API.StopRequested:
        if API.HasGump(SET_PERMISSION_GUMP_ID):
            API.ReplyGump(2)
        API.Pause(0.1)
