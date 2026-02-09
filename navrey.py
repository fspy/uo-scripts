import API

while not API.StopRequested:
    stones = API.GetItemsOnGround(3, 0x03BF) or []
    for stone in stones:
        API.HeadMsg("CLICKED", stone)
        API.UseObject(stone, True)
        API.Pause(1)
        break
    API.Pause(0.1)
