# add 0x0DF9 to scavenger!
cotton_ids = (3153, 3154, 3155, 3156)

def find_cotton():
    return [item 
        for id in cotton_ids
        for item in Items.FindAllByID(id, -1, -1, -1)
    ]

def distance(a, b):
    return Misc.Distance(a.Position.X, a.Position.Y, b.Position.X, b.Position.Y)

def closest_cotton(l):
    cl = l[:]
    cl.sort(key=lambda i: -distance(Player, i))
    if len(cl) > 0:
        return cl.pop()
    return None

if not Scavenger.Status():
    Scavenger.Start()

while not Player.IsGhost:
    cotton_list = find_cotton()
    closest = closest_cotton(cotton_list)

    if not closest:
        Player.HeadMessage(33, "Didn't find any cotton nearby!")
        break
        # Misc.Pause(1000)
        # continue

    Items.Message(closest, 1150, 'Over here!')

    if distance(closest, Player) > 2:
        Player.PathFindTo(closest.Position)
        while distance(closest, Player) > 1:
            Misc.Pause(1200)

    Items.UseItem(closest)
    Misc.Pause(600)