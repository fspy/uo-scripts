import API

x, y = API.Player.X, API.Player.Y
while True:
    if API.Player.X == x and API.Player.Y == y:
        API.Pause(0.1)
        continue

    pos = (API.Player.X - x, API.Player.Y - y)
    x, y = API.Player.X, API.Player.Y

    while not API.InJournalAny(
        ["cannot be seen", "too far away", "sand here to mine"], True
    ):
        API.UseType(0x0F39)
        if API.WaitForTarget():
            API.TargetLandRel(*pos)
            API.Pause(0.5)
