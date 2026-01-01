import API

if not API.GetPersistentVar("Mount", "", API.PersistentVar.Char):
    if API.Player.Mount:
        API.Dismount(skipQueue=True)
        API.Pause(0.6)
    API.HeadMsg("Click your mount", API.Player)
    tar = API.RequestTarget(timeout=10)
    if tar:
        API.SavePersistentVar("Mount", str(tar), API.PersistentVar.Char)
        API.HeadMsg(f"Mount stored {tar}", API.Player)
        API.UseObject(tar)


API.UseObject(
    API.Player
    if API.Player.Mount
    else int(API.GetPersistentVar("Mount", "", API.PersistentVar.Char)),
    skipQueue=True,
)
