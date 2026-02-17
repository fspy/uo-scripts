import API

PLANT_TYPES = (
    0x0CA5,
    0x0C83,
    0x0C9F,
    0x0CFB,
    0x246C,
    0x0D27,
)
done = []


def grab_resources(plant):
    API.UseObject(plant)
    while not API.HasGump(0xA9B90129):
        API.Pause(0.05)
    API.ReplyGump(1, 0xA9B90129)
    while not API.HasGump(0x66E3F765):
        API.Pause(0.05)
    API.ReplyGump(7, 0x66E3F765)
    while not API.HasGump(0x66E3F765):
        API.Pause(0.05)
    API.ReplyGump(8, 0x66E3F765)
    while not API.HasGump(0x66E3F765):
        API.Pause(0.05)
    API.ReplyGump(0, 0x66E3F765)


while not API.StopRequested:
    plants = filter(
        lambda x: x.Graphic in PLANT_TYPES and x.Serial not in done,
        API.GetItemsOnGround(2),
    )

    for plant in plants:
        grab_resources(plant)
        done.append(plant.Serial)
        plant.SetHue(1153)
        API.Pause(0.05)

    API.Pause(0.05)
