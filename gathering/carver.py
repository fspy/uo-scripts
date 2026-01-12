import API

cleaver = API.FindType(0x2D2F, API.Backpack, hue=0)
corpses = []


def carve(corpse):
    API.UseObject(cleaver.Serial, True)
    API.WaitForTarget(timeout=2)
    API.Target(corpse)  # pyright:ignore

    API.HeadMsg("Carving!", corpse, 1161)
    API.Pause(0.6)

    if API.InJournalAny(["skin it and place", "carve some", "nothing useful"], True):
        return True
    return False


while not API.StopRequested:
    if not cleaver:
        API.SysMsg("cleaver not found, exiting")
        API.Stop()

    corpse = API.NearestCorpse(1)
    if not corpse or corpse.Serial in corpses:
        continue

    if carve(corpse.Serial):
        API.IgnoreObject(corpse.Serial)
        corpses.append(corpse.Serial)

    API.Pause(0.05)
